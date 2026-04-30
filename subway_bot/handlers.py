from __future__ import annotations

import asyncio
import html
import io
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from subway_bot.builders import (
    NUMERIC_BUILDERS,
    UserInputError,
    build_inventory_prompt,
    build_numeric_prompt,
    expand_number_ranges,
    parse_inventory_input,
    parse_numeric_input,
)
from subway_bot.catalogs import CatalogError, CatalogRepository
from subway_bot.config import Settings
from subway_bot.constants import CATALOG_KIND_ALIASES, SUPPORTED_EDITABLE_DOCUMENTS
from subway_bot.documents import (
    DocumentParseError,
    parse_character_document,
    parse_hoverboard_document,
    parse_wallet_document,
)
from subway_bot.i18n import ar
from subway_bot.savefiles import (
    build_badges,
    build_character_inventory,
    build_hoverboard_inventory,
    build_profile_inventory,
    build_top_run,
    build_upgrades,
    build_user_stats,
    build_wallet,
)

logger = logging.getLogger(__name__)

AWAITING_INPUT = 1

FLOW_TITLES = {
    "wallet": ar("المحفظة"),
    "characters": ar("الشخصيات"),
    "hoverboards": ar("ألواح التزلج"),
    "portraits": ar("الصور الشخصية"),
    "frames": ar("الإطارات"),
    "badges": ar("الشارات"),
    "upgrades": ar("التطويرات"),
    "toprun": ar("أعلى نتيجة"),
}

CATALOG_TITLES = {
    "characters": ar("فهرس الشخصيات"),
    "hoverboards": ar("فهرس ألواح التزلج"),
    "portraits": ar("فهرس الصور الشخصية"),
    "frames": ar("فهرس الإطارات"),
}

FULL_SELECTION_VALUES = {
    "all",
    ar("الكل"),
    ar("جميع"),
    ar("الجميع"),
}


class BotHandlers:
    def __init__(self, *, settings: Settings, catalogs: CatalogRepository) -> None:
        self.settings = settings
        self.catalogs = catalogs

    def register(self, application: Application) -> None:
        conversation = ConversationHandler(
            entry_points=[
                CommandHandler("wallet", self.start_wallet),
                CommandHandler("characters", self.start_characters),
                CommandHandler("characters_all", self.start_characters_all),
                CommandHandler("hoverboards", self.start_hoverboards),
                CommandHandler("hoverboards_all", self.start_hoverboards_all),
                CommandHandler("portraits", self.start_portraits),
                CommandHandler("frames", self.start_frames),
                CommandHandler("badges", self.start_badges),
                CommandHandler("upgrades", self.start_upgrades),
                CommandHandler("toprun", self.start_toprun),
                CallbackQueryHandler(self.menu_action, pattern=r"^menu:"),
                MessageHandler(filters.Document.ALL, self.start_document_edit),
            ],
            states={
                AWAITING_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_input),
                    CallbackQueryHandler(self.menu_action, pattern=r"^menu:"),
                    MessageHandler(filters.Document.ALL, self.start_document_edit),
                ]
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                CallbackQueryHandler(self.menu_action, pattern=r"^menu:cancel$"),
            ],
            allow_reentry=True,
            name="subway_builder",
        )

        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("menu", self.start))
        application.add_handler(CommandHandler("help", self.help))
        application.add_handler(CommandHandler("catalog", self.catalog))
        application.add_handler(CommandHandler("cancel", self.cancel))
        application.add_handler(conversation)
        application.add_error_handler(self.error_handler)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._authorize(update):
            return

        text = ar(
            "<b>واجهة Subway Surfers العربية</b>\n"
            "<i>بوت أنيق لتجهيز ملفات الحفظ وتعديلها بسرعة وبشكل مرتب.</i>\n\n"
            "<b>الخدمات المتاحة</b>\n"
            "- إنشاء ملفات المحفظة والموارد\n"
            "- فتح الشخصيات وألواح التزلج\n"
            "- إنشاء ملفات الصور الشخصية والإطارات\n"
            "- تعديل ملفات مرفوعة جاهزة\n\n"
            "<b>رفع الملفات المدعومة</b>\n"
            "<code>wallet.json</code>\n"
            "<code>characters_inventory.json</code>\n"
            "<code>boards_inventory.json</code>\n\n"
            "اختر ما تريد من القائمة التالية."
        )
        await self._reply_text(update, text, reply_markup=self._main_menu_markup())

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._authorize(update):
            return

        text = ar(
            "<b>طريقة الاستخدام</b>\n\n"
            "1. اختر القسم من الأزرار أو عبر الأوامر.\n"
            "2. أرسل القيم المطلوبة بنفس المفاتيح الإنجليزية الظاهرة في القالب.\n"
            "3. سيعيد البوت ملف JSON جاهزًا للتحميل.\n\n"
            "<b>أمثلة مفيدة</b>\n"
            "- <code>/catalog characters 1</code>\n"
            "- <code>/catalog شخصيات 1</code>\n"
            "- <code>owned=all</code>\n"
            "- <code>owned=1-5,8,10</code>\n\n"
            "<b>مكان وضع الملفات داخل أندرويد</b>\n"
            "<code>Android &gt; data &gt; com.kiloo.subwaysurf &gt; files &gt; profile</code>"
        )
        await self._reply_text(update, text, reply_markup=self._secondary_menu_markup())

    async def catalog(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._authorize(update):
            return

        if not context.args:
            await self._reply_text(
                update,
                ar(
                    "الاستخدام الصحيح:\n"
                    "<code>/catalog characters 1</code>\n"
                    "<code>/catalog شخصيات 1</code>"
                ),
                reply_markup=self._catalog_shortcuts_markup(),
            )
            return

        raw_kind = (
            " ".join(context.args[:-1])
            if len(context.args) > 1 and context.args[-1].isdigit()
            else " ".join(context.args)
        )
        page_arg = context.args[-1] if len(context.args) > 1 and context.args[-1].isdigit() else None

        kind = CATALOG_KIND_ALIASES.get(raw_kind.strip().lower()) or CATALOG_KIND_ALIASES.get(
            raw_kind.strip()
        )
        if kind is None:
            await self._reply_text(
                update,
                ar("نوع الفهرس غير معروف. استخدم: الشخصيات، ألواح التزلج، الصور، أو الإطارات."),
                reply_markup=self._catalog_shortcuts_markup(),
            )
            return

        try:
            page = int(page_arg) if page_arg else 1
        except ValueError:
            await self._reply_text(update, ar("رقم الصفحة يجب أن يكون رقمًا صحيحًا."))
            return

        try:
            text = await asyncio.to_thread(self._build_catalog_message, kind, page)
        except CatalogError as exc:
            await self._reply_text(update, html.escape(str(exc)))
            return

        await self._reply_text(update, text, reply_markup=self._catalog_shortcuts_markup())

    async def menu_action(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not await self._authorize(update):
            return ConversationHandler.END

        query = update.callback_query
        if query is None or query.data is None:
            return ConversationHandler.END

        await query.answer()
        action = query.data.removeprefix("menu:")

        if action == "home":
            await self.start(update, context)
            return ConversationHandler.END
        if action == "help":
            await self.help(update, context)
            return ConversationHandler.END
        if action == "cancel":
            return await self.cancel(update, context)
        if action == "wallet":
            return await self.start_wallet(update, context)
        if action == "characters":
            return await self.start_characters(update, context)
        if action == "characters_all":
            return await self.start_characters_all(update, context)
        if action == "hoverboards":
            return await self.start_hoverboards(update, context)
        if action == "hoverboards_all":
            return await self.start_hoverboards_all(update, context)
        if action == "portraits":
            return await self.start_portraits(update, context)
        if action == "frames":
            return await self.start_frames(update, context)
        if action == "badges":
            return await self.start_badges(update, context)
        if action == "upgrades":
            return await self.start_upgrades(update, context)
        if action == "toprun":
            return await self.start_toprun(update, context)
        if action.startswith("catalog:"):
            _, kind, page = action.split(":", 2)
            try:
                text = await asyncio.to_thread(self._build_catalog_message, kind, int(page))
            except CatalogError as exc:
                await self._reply_text(update, html.escape(str(exc)))
                return ConversationHandler.END
            await self._reply_text(update, text, reply_markup=self._catalog_shortcuts_markup())
            return ConversationHandler.END

        await self._reply_text(update, ar("هذا الخيار غير معروف حاليًا."))
        return ConversationHandler.END

    async def start_wallet(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        return await self._start_numeric_flow("wallet", update, context)

    async def start_badges(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        return await self._start_numeric_flow("badges", update, context)

    async def start_upgrades(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        return await self._start_numeric_flow("upgrades", update, context)

    async def start_toprun(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        return await self._start_numeric_flow("toprun", update, context)

    async def start_characters(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        return await self._start_inventory_flow("characters", update, context)

    async def start_hoverboards(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        return await self._start_inventory_flow("hoverboards", update, context)

    async def start_portraits(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        return await self._start_inventory_flow("portraits", update, context)

    async def start_frames(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        return await self._start_inventory_flow("frames", update, context)

    async def start_characters_all(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not await self._authorize(update):
            return ConversationHandler.END

        await self._generate_full_inventory(update, "characters")
        return ConversationHandler.END

    async def start_hoverboards_all(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not await self._authorize(update):
            return ConversationHandler.END

        await self._generate_full_inventory(update, "hoverboards")
        return ConversationHandler.END

    async def start_document_edit(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not await self._authorize(update):
            return ConversationHandler.END

        message = self._message(update)
        document = message.document if message else None
        if document is None:
            return ConversationHandler.END

        file_name = (document.file_name or "").lower()
        kind = SUPPORTED_EDITABLE_DOCUMENTS.get(file_name)
        if kind is None:
            await self._reply_text(
                update,
                ar(
                    "أستطيع تعديل الملفات التالية فقط:\n"
                    "<code>wallet.json</code>\n"
                    "<code>characters_inventory.json</code>\n"
                    "<code>boards_inventory.json</code>"
                ),
                reply_markup=self._secondary_menu_markup(),
            )
            return ConversationHandler.END

        try:
            payload = await self._download_document(document)
            if kind == "wallet":
                initial_values = parse_wallet_document(payload)
                return await self._start_numeric_flow(
                    "wallet",
                    update,
                    context,
                    initial_values=initial_values,
                    preface=ar("تمت قراءة ملف المحفظة. عدّل القيم ثم أرسلها من جديد."),
                )

            if kind == "characters":
                owned_ids, selected_id = parse_character_document(payload)
                owned_numbers = await asyncio.to_thread(
                    self.catalogs.resolve_ids_to_numbers,
                    "characters",
                    owned_ids,
                )
                selected_number = await asyncio.to_thread(
                    self.catalogs.resolve_id_to_number,
                    "characters",
                    selected_id,
                )
                return await self._start_inventory_flow(
                    "characters",
                    update,
                    context,
                    owned_numbers=owned_numbers,
                    selected_number=selected_number,
                    preface=ar(
                        "تمت قراءة ملف الشخصيات. يمكنك تعديل القائمة أو فتح الجميع مباشرة."
                    ),
                )

            owned_ids, selected_id = parse_hoverboard_document(payload)
            owned_numbers = await asyncio.to_thread(
                self.catalogs.resolve_ids_to_numbers,
                "hoverboards",
                owned_ids,
            )
            selected_number = await asyncio.to_thread(
                self.catalogs.resolve_id_to_number,
                "hoverboards",
                selected_id,
            )
            return await self._start_inventory_flow(
                "hoverboards",
                update,
                context,
                owned_numbers=owned_numbers,
                selected_number=selected_number,
                preface=ar(
                    "تمت قراءة ملف ألواح التزلج. يمكنك تعديل القائمة أو فتح الجميع مباشرة."
                ),
            )
        except (DocumentParseError, CatalogError) as exc:
            await self._reply_text(update, html.escape(str(exc)))
            return ConversationHandler.END

    async def receive_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not await self._authorize(update):
            return ConversationHandler.END

        kind = context.user_data.get("builder_kind")
        if kind is None:
            await self._reply_text(
                update,
                ar(
                    "لا توجد عملية نشطة الآن. اختر من القائمة الرئيسية أو استخدم <code>/help</code>."
                ),
                reply_markup=self._main_menu_markup(),
            )
            return ConversationHandler.END

        try:
            if kind in NUMERIC_BUILDERS:
                await self._handle_numeric_submission(kind, update)
            else:
                await self._handle_inventory_submission(kind, update)
        except (UserInputError, CatalogError) as exc:
            await self._reply_text(
                update,
                f"{html.escape(str(exc))}\n\n{ar('أرسل القالب مرة أخرى أو اختر إلغاء.')}",
                reply_markup=self._flow_cancel_markup(),
            )
            return AWAITING_INPUT

        context.user_data.clear()
        await self._reply_text(
            update,
            ar("<b>تم التنفيذ بنجاح</b>\nيمكنك اختيار عملية جديدة من القائمة."),
            reply_markup=self._main_menu_markup(),
        )
        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data.clear()
        await self._reply_text(
            update,
            ar("تم إلغاء العملية الحالية."),
            reply_markup=self._main_menu_markup(),
        )
        return ConversationHandler.END

    async def error_handler(
        self, update: object, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        logger.exception("Unhandled bot error", exc_info=context.error)
        if isinstance(update, Update):
            message = self._message(update)
            if message is not None:
                try:
                    await message.reply_text(
                        ar("حدث خطأ غير متوقع أثناء تنفيذ الطلب. حاول مرة أخرى بعد قليل.")
                    )
                except Exception:
                    logger.exception("Failed to notify the user about an error.")

    async def _start_numeric_flow(
        self,
        kind: str,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        *,
        initial_values: dict[str, int] | None = None,
        preface: str | None = None,
    ) -> int:
        if not await self._authorize(update):
            return ConversationHandler.END

        context.user_data["builder_kind"] = kind
        prompt = build_numeric_prompt(kind, initial_values)
        title = FLOW_TITLES[kind]
        message = self._format_prompt(title, prompt, preface=preface)
        await self._reply_text(update, message, reply_markup=self._flow_menu_markup(kind))
        return AWAITING_INPUT

    async def _start_inventory_flow(
        self,
        kind: str,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        *,
        owned_numbers: list[int] | None = None,
        selected_number: int | None = None,
        preface: str | None = None,
    ) -> int:
        if not await self._authorize(update):
            return ConversationHandler.END

        context.user_data["builder_kind"] = kind
        prompt = build_inventory_prompt(
            kind,
            owned_numbers=owned_numbers,
            selected_number=selected_number,
        )
        title = FLOW_TITLES[kind]
        message = self._format_prompt(title, prompt, preface=preface)
        await self._reply_text(update, message, reply_markup=self._flow_menu_markup(kind))
        return AWAITING_INPUT

    async def _handle_numeric_submission(self, kind: str, update: Update) -> None:
        values = parse_numeric_input(kind, self._incoming_text(update))

        if kind == "wallet":
            await self._send_document(
                update,
                filename="wallet.json",
                payload=build_wallet(values),
                caption=ar("<b>تم تجهيز ملف المحفظة</b>\n<code>wallet.json</code>"),
            )
            return

        if kind == "badges":
            await self._send_document(
                update,
                filename="user_stats.json",
                payload=build_badges(values),
                caption=ar("<b>تم تجهيز ملف الشارات</b>\n<code>user_stats.json</code>"),
            )
            return

        if kind == "upgrades":
            await self._send_document(
                update,
                filename="upgrades.json",
                payload=build_upgrades(values),
                caption=ar("<b>تم تجهيز ملف التطويرات</b>\n<code>upgrades.json</code>"),
            )
            return

        await self._send_document(
            update,
            filename="top_run.json",
            payload=build_top_run(values),
            caption=ar("<b>تم تجهيز ملف أعلى نتيجة</b>\n<code>top_run.json</code>"),
        )
        await self._send_document(
            update,
            filename="user_stats.json",
            payload=build_user_stats(values["userstatsAmount"]),
            caption=ar("<b>تم تجهيز ملف الإحصائيات المرافق</b>\n<code>user_stats.json</code>"),
        )

    async def _handle_inventory_submission(self, kind: str, update: Update) -> None:
        parsed = parse_inventory_input(self._incoming_text(update))
        catalog = await asyncio.to_thread(self.catalogs.get_catalog, kind)
        all_numbers = [entry.number for entry in catalog]

        owned_value = parsed.owned_spec.strip()
        if owned_value.lower() in FULL_SELECTION_VALUES or owned_value in FULL_SELECTION_VALUES:
            owned_numbers = all_numbers
        else:
            owned_numbers = expand_number_ranges(parsed.owned_spec)

        if parsed.selected not in owned_numbers:
            raise UserInputError(ar("يجب أن تكون قيمة `selected` موجودة أيضًا داخل `owned`."))

        owned_entries = await asyncio.to_thread(
            self.catalogs.resolve_numbers,
            kind,
            owned_numbers,
        )
        selected_entry = (
            await asyncio.to_thread(
                self.catalogs.resolve_numbers,
                kind,
                [parsed.selected],
            )
        )[0]

        if kind == "characters":
            payload = build_character_inventory(selected_entry, owned_entries)
            filename = "characters_inventory.json"
            caption = ar("<b>تم تجهيز ملف الشخصيات</b>\n") + (
                f"{ar('المختار افتراضيًا:')} <code>{html.escape(selected_entry.name)}</code>"
            )
        elif kind == "hoverboards":
            payload = build_hoverboard_inventory(selected_entry, owned_entries)
            filename = "boards_inventory.json"
            caption = ar("<b>تم تجهيز ملف ألواح التزلج</b>\n") + (
                f"{ar('المختار افتراضيًا:')} <code>{html.escape(selected_entry.name)}</code>"
            )
        elif kind == "portraits":
            payload = build_profile_inventory(selected=selected_entry, owned=owned_entries)
            filename = "profile_portrait.json"
            caption = ar("<b>تم تجهيز ملف الصور الشخصية</b>\n<code>profile_portrait.json</code>")
        else:
            payload = build_profile_inventory(selected=selected_entry, owned=owned_entries)
            filename = "profile_frame.json"
            caption = ar("<b>تم تجهيز ملف الإطارات</b>\n<code>profile_frame.json</code>")

        await self._send_document(update, filename=filename, payload=payload, caption=caption)

    async def _generate_full_inventory(self, update: Update, kind: str) -> None:
        catalog = await asyncio.to_thread(self.catalogs.get_catalog, kind)
        if not catalog:
            raise CatalogError(ar("القائمة المطلوبة فارغة حاليًا."))

        selected_entry = catalog[0]
        if kind == "characters":
            payload = build_character_inventory(selected_entry, catalog)
            filename = "characters_inventory.json"
            caption = ar("<b>تم فتح كل الشخصيات</b>\n") + (
                f"{ar('الافتراضي الحالي:')} <code>{html.escape(selected_entry.name)}</code>"
            )
        else:
            payload = build_hoverboard_inventory(selected_entry, catalog)
            filename = "boards_inventory.json"
            caption = ar("<b>تم فتح كل ألواح التزلج</b>\n") + (
                f"{ar('الافتراضي الحالي:')} <code>{html.escape(selected_entry.name)}</code>"
            )

        await self._send_document(update, filename=filename, payload=payload, caption=caption)
        await self._reply_text(
            update,
            ar(
                "إذا أردت تغيير العنصر الافتراضي، افتح القسم نفسه وأرسل `selected=<رقم>` يدويًا."
            ),
            reply_markup=self._main_menu_markup(),
        )

    async def _authorize(self, update: Update) -> bool:
        if not self.settings.allowed_user_ids:
            return True

        user = update.effective_user
        if user and user.id in self.settings.allowed_user_ids:
            return True

        if update.callback_query is not None:
            await update.callback_query.answer()
        await self._reply_text(update, ar("هذا البوت مقيد لمستخدمين محددين فقط."))
        return False

    async def _download_document(self, document) -> bytes:
        telegram_file = await document.get_file()
        buffer = io.BytesIO()
        await telegram_file.download_to_memory(out=buffer)
        return buffer.getvalue()

    async def _send_document(
        self,
        update: Update,
        *,
        filename: str,
        payload: str,
        caption: str,
    ) -> None:
        file_buffer = io.BytesIO(payload.encode("utf-8"))
        file_buffer.seek(0)
        message = self._message(update)
        if message is None:
            return
        await message.reply_document(
            document=InputFile(file_buffer, filename=filename),
            caption=caption,
        )

    def _build_catalog_message(self, kind: str, page: int) -> str:
        if page <= 0:
            raise CatalogError(ar("رقم الصفحة يبدأ من 1."))

        catalog = self.catalogs.get_catalog(kind)
        total_pages = max(
            1,
            (len(catalog) + self.settings.catalog_page_size - 1)
            // self.settings.catalog_page_size,
        )
        if page > total_pages:
            raise CatalogError(ar(f"هذه الصفحة غير موجودة. آخر صفحة هي {total_pages}."))

        start_index = (page - 1) * self.settings.catalog_page_size
        end_index = start_index + self.settings.catalog_page_size
        page_items = catalog[start_index:end_index]

        lines = [
            f"<b>{CATALOG_TITLES[kind]}</b>",
            ar(f"الصفحة {page} من {total_pages}"),
            "",
        ]
        lines.extend(
            f"<code>{entry.number}</code> — {html.escape(entry.name)}"
            for entry in page_items
        )
        return "\n".join(lines)

    def _format_prompt(self, title: str, prompt: str, *, preface: str | None = None) -> str:
        blocks = [f"<b>{html.escape(title)}</b>"]
        if preface:
            blocks.append(html.escape(preface))
        blocks.append(ar("أرسل البيانات كما هي داخل القالب التالي:"))
        blocks.append(f"<pre>{html.escape(prompt)}</pre>")
        return "\n\n".join(blocks)

    def _main_menu_markup(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(ar("المحفظة"), callback_data="menu:wallet"),
                    InlineKeyboardButton(ar("الشخصيات"), callback_data="menu:characters"),
                ],
                [
                    InlineKeyboardButton(ar("ألواح التزلج"), callback_data="menu:hoverboards"),
                    InlineKeyboardButton(ar("الشارات"), callback_data="menu:badges"),
                ],
                [
                    InlineKeyboardButton(ar("الصور الشخصية"), callback_data="menu:portraits"),
                    InlineKeyboardButton(ar("الإطارات"), callback_data="menu:frames"),
                ],
                [
                    InlineKeyboardButton(ar("التطويرات"), callback_data="menu:upgrades"),
                    InlineKeyboardButton(ar("أعلى نتيجة"), callback_data="menu:toprun"),
                ],
                [
                    InlineKeyboardButton(ar("فتح كل الشخصيات"), callback_data="menu:characters_all"),
                    InlineKeyboardButton(ar("فتح كل الألواح"), callback_data="menu:hoverboards_all"),
                ],
                [
                    InlineKeyboardButton(ar("فهرس الشخصيات"), callback_data="menu:catalog:characters:1"),
                    InlineKeyboardButton(ar("فهرس الألواح"), callback_data="menu:catalog:hoverboards:1"),
                ],
                [
                    InlineKeyboardButton(ar("المساعدة"), callback_data="menu:help"),
                ],
            ]
        )

    def _secondary_menu_markup(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(ar("القائمة الرئيسية"), callback_data="menu:home"),
                    InlineKeyboardButton(ar("فهرس الشخصيات"), callback_data="menu:catalog:characters:1"),
                ]
            ]
        )

    def _catalog_shortcuts_markup(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(ar("الشخصيات"), callback_data="menu:catalog:characters:1"),
                    InlineKeyboardButton(ar("الألواح"), callback_data="menu:catalog:hoverboards:1"),
                ],
                [
                    InlineKeyboardButton(ar("الصور"), callback_data="menu:catalog:portraits:1"),
                    InlineKeyboardButton(ar("الإطارات"), callback_data="menu:catalog:frames:1"),
                ],
                [
                    InlineKeyboardButton(ar("القائمة الرئيسية"), callback_data="menu:home"),
                ],
            ]
        )

    def _flow_cancel_markup(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(ar("إلغاء"), callback_data="menu:cancel"),
                    InlineKeyboardButton(ar("القائمة الرئيسية"), callback_data="menu:home"),
                ]
            ]
        )

    def _flow_menu_markup(self, kind: str) -> InlineKeyboardMarkup:
        rows: list[list[InlineKeyboardButton]] = []

        if kind == "characters":
            rows.append(
                [
                    InlineKeyboardButton(ar("فتح كل الشخصيات"), callback_data="menu:characters_all"),
                    InlineKeyboardButton(ar("فهرس الشخصيات"), callback_data="menu:catalog:characters:1"),
                ]
            )
        elif kind == "hoverboards":
            rows.append(
                [
                    InlineKeyboardButton(ar("فتح كل الألواح"), callback_data="menu:hoverboards_all"),
                    InlineKeyboardButton(ar("فهرس الألواح"), callback_data="menu:catalog:hoverboards:1"),
                ]
            )
        elif kind == "portraits":
            rows.append(
                [
                    InlineKeyboardButton(ar("فهرس الصور"), callback_data="menu:catalog:portraits:1"),
                ]
            )
        elif kind == "frames":
            rows.append(
                [
                    InlineKeyboardButton(ar("فهرس الإطارات"), callback_data="menu:catalog:frames:1"),
                ]
            )

        rows.append(
            [
                InlineKeyboardButton(ar("القائمة الرئيسية"), callback_data="menu:home"),
                InlineKeyboardButton(ar("إلغاء"), callback_data="menu:cancel"),
            ]
        )
        return InlineKeyboardMarkup(rows)

    async def _reply_text(
        self,
        update: Update,
        text: str,
        *,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> None:
        message = self._message(update)
        if message is None:
            return
        await message.reply_text(text, reply_markup=reply_markup)

    def _message(self, update: Update):
        if update.effective_message is not None:
            return update.effective_message
        if update.callback_query is not None:
            return update.callback_query.message
        return None

    def _incoming_text(self, update: Update) -> str:
        message = self._message(update)
        return message.text if message and message.text else ""
