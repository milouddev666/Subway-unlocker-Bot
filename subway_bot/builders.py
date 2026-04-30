from __future__ import annotations

from dataclasses import dataclass

from subway_bot.constants import (
    DEFAULT_UPGRADE_EXPIRATION,
    MAX_SIGNED_32,
    MAX_SIGNED_63,
)
from subway_bot.i18n import ar


class UserInputError(ValueError):
    """Raised when a user payload is invalid."""


@dataclass(frozen=True)
class FieldSpec:
    name: str
    min_value: int
    max_value: int
    default: int | None = None
    copy_from: str | None = None


@dataclass(frozen=True)
class NumericBuilderDefinition:
    kind: str
    filename: str
    fields: tuple[FieldSpec, ...]
    intro: str


@dataclass(frozen=True)
class InventoryInput:
    owned_spec: str
    selected: int


NUMERIC_BUILDERS = {
    "wallet": NumericBuilderDefinition(
        kind="wallet",
        filename="wallet.json",
        intro=ar(
            "أرسل قيم المحفظة سطرًا بسطر بصيغة `key=value`.\n"
            "احتفظ بأسماء المفاتيح الإنجليزية كما هي.\n\n"
            "مثال:\n"
            "hoverboards=999\n"
            "gamekeys=999\n"
            "gamecoins=1000000\n"
            "scoreboosters=99\n"
            "headstarts=99\n"
            "eventcoins=5000"
        ),
        fields=(
            FieldSpec("hoverboards", 1, MAX_SIGNED_32),
            FieldSpec("gamekeys", 1, MAX_SIGNED_32),
            FieldSpec("gamecoins", 1, MAX_SIGNED_32),
            FieldSpec("scoreboosters", 1, MAX_SIGNED_32),
            FieldSpec("headstarts", 1, MAX_SIGNED_32),
            FieldSpec("eventcoins", 1, MAX_SIGNED_32),
        ),
    ),
    "badges": NumericBuilderDefinition(
        kind="badges",
        filename="user_stats.json",
        intro=ar(
            "أرسل أرقام الشارات بصيغة `key=value`.\n"
            "احتفظ بأسماء المفاتيح الإنجليزية كما هي.\n\n"
            "مثال:\n"
            "bronze=10\n"
            "silver=9\n"
            "gold=8\n"
            "diamond=7\n"
            "champ=6"
        ),
        fields=(
            FieldSpec("bronze", 1, MAX_SIGNED_32),
            FieldSpec("silver", 1, MAX_SIGNED_32),
            FieldSpec("gold", 1, MAX_SIGNED_32),
            FieldSpec("diamond", 1, MAX_SIGNED_32),
            FieldSpec("champ", 1, MAX_SIGNED_32),
        ),
    ),
    "upgrades": NumericBuilderDefinition(
        kind="upgrades",
        filename="upgrades.json",
        intro=ar(
            "أرسل قيم التطويرات بصيغة `key=value`.\n"
            "يمكنك ترك الحقول الاختيارية الخاصة بالـ boost فارغة لاستخدام القيم الطويلة الافتراضية.\n\n"
            "jetpack=6\n"
            "superSneakers=6\n"
            "magnet=6\n"
            "doubleScore=6\n"
            "doubleCoinsAmount=1\n"
        )
        + f"\ndoubleCoinsTime={DEFAULT_UPGRADE_EXPIRATION}\n"
        + ar("tokenBoostAmount=1\n")
        + f"tokenBoostTime={DEFAULT_UPGRADE_EXPIRATION}",
        fields=(
            FieldSpec("jetpack", 1, 6),
            FieldSpec("superSneakers", 1, 6),
            FieldSpec("magnet", 1, 6),
            FieldSpec("doubleScore", 1, 6),
            FieldSpec("doubleCoinsAmount", 0, 100, default=1),
            FieldSpec(
                "doubleCoinsTime",
                0,
                DEFAULT_UPGRADE_EXPIRATION,
                default=DEFAULT_UPGRADE_EXPIRATION,
            ),
            FieldSpec("tokenBoostAmount", 0, 100, default=1),
            FieldSpec(
                "tokenBoostTime",
                0,
                DEFAULT_UPGRADE_EXPIRATION,
                default=DEFAULT_UPGRADE_EXPIRATION,
            ),
        ),
    ),
    "toprun": NumericBuilderDefinition(
        kind="toprun",
        filename="top_run.json",
        intro=ar(
            "أرسل قيم أعلى نتيجة بصيغة `key=value`.\n"
            "الحقل `userstatsAmount` اختياري، وإذا تركته فارغًا سيأخذ نفس قيمة `highscore`.\n\n"
            "highscore=123456789\n"
            "userstatsAmount=123456789"
        ),
        fields=(
            FieldSpec("highscore", 0, MAX_SIGNED_63),
            FieldSpec("userstatsAmount", 0, MAX_SIGNED_32, copy_from="highscore"),
        ),
    ),
}

INVENTORY_INTROS = {
    "characters": ar(
        "أرسل اختيار الشخصيات بصيغة `key=value`.\n"
        "لرؤية الأرقام استخدم `/catalog characters 1` أو `/catalog شخصيات 1`.\n"
        "يمكنك كتابة `owned=all` أو `owned=الكل` لفتح الجميع.\n\n"
        "owned=1-5,9,12\nselected=1"
    ),
    "hoverboards": ar(
        "أرسل اختيار ألواح التزلج بصيغة `key=value`.\n"
        "لرؤية الأرقام استخدم `/catalog hoverboards 1` أو `/catalog ألواح 1`.\n"
        "يمكنك كتابة `owned=all` أو `owned=الكل` لفتح الجميع.\n\n"
        "owned=1-3,9\nselected=1"
    ),
    "portraits": ar(
        "أرسل اختيار الصور الشخصية بصيغة `key=value`.\n"
        "لرؤية الأرقام استخدم `/catalog portraits 1` أو `/catalog صور 1`.\n\n"
        "owned=1-5,8\nselected=1"
    ),
    "frames": ar(
        "أرسل اختيار الإطارات بصيغة `key=value`.\n"
        "لرؤية الأرقام استخدم `/catalog frames 1` أو `/catalog إطارات 1`.\n\n"
        "owned=1-4,10\nselected=1"
    ),
}


def parse_assignment_block(text: str) -> dict[str, str]:
    assignments: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        normalized = line.replace("\uff1a", ":")
        if "=" in normalized:
            key, value = normalized.split("=", 1)
        elif ":" in normalized:
            key, value = normalized.split(":", 1)
        else:
            raise UserInputError(
                ar("الصيغة غير صحيحة. استخدم `key=value` في هذا السطر: ") + f"`{line}`"
            )
        key = key.strip()
        value = value.strip()
        if not key:
            raise UserInputError(ar("لا يمكن ترك اسم المفتاح فارغًا."))
        assignments[key] = value
    if not assignments:
        raise UserInputError(ar("لم يتم إرسال أي قيم."))
    return assignments


def parse_numeric_input(kind: str, text: str) -> dict[str, int]:
    definition = NUMERIC_BUILDERS[kind]
    assignments = parse_assignment_block(text)
    allowed_keys = {field.name for field in definition.fields}

    unknown = sorted(set(assignments) - allowed_keys)
    if unknown:
        raise UserInputError(ar("حقول غير معروفة: ") + ", ".join(unknown))

    values: dict[str, int] = {}
    for field in definition.fields:
        raw_value = assignments.get(field.name)
        if raw_value is None or raw_value == "":
            if field.default is not None:
                values[field.name] = field.default
                continue
            if field.copy_from is not None:
                if field.copy_from not in values:
                    raise UserInputError(
                        ar("الحقل ") + f"`{field.name}` " + ar("يعتمد على ") + f"`{field.copy_from}` " + ar("لكنه غير موجود.")
                    )
                values[field.name] = values[field.copy_from]
                continue
            raise UserInputError(ar("الحقل ") + f"`{field.name}` " + ar("مطلوب."))

        try:
            parsed = int(raw_value)
        except ValueError as exc:
            raise UserInputError(
                ar("الحقل ") + f"`{field.name}` " + ar("يجب أن يكون رقمًا صحيحًا.")
            ) from exc

        if parsed < field.min_value or parsed > field.max_value:
            raise UserInputError(
                ar(
                    f"الحقل `{field.name}` يجب أن يكون بين {field.min_value} و {field.max_value}."
                )
            )

        values[field.name] = parsed

    return values


def parse_inventory_input(text: str) -> InventoryInput:
    assignments = parse_assignment_block(text)
    allowed_keys = {"owned", "selected"}
    unknown = sorted(set(assignments) - allowed_keys)
    if unknown:
        raise UserInputError(ar("حقول غير معروفة: ") + ", ".join(unknown))

    owned_spec = assignments.get("owned", "").strip()
    if not owned_spec:
        raise UserInputError(ar("الحقل `owned` مطلوب."))

    selected_raw = assignments.get("selected", "").strip()
    if not selected_raw:
        raise UserInputError(ar("الحقل `selected` مطلوب."))

    try:
        selected = int(selected_raw)
    except ValueError as exc:
        raise UserInputError(ar("الحقل `selected` يجب أن يكون رقمًا صحيحًا.")) from exc

    if selected <= 0:
        raise UserInputError(ar("الحقل `selected` يجب أن يكون رقمًا أكبر من صفر."))

    return InventoryInput(owned_spec=owned_spec, selected=selected)


def expand_number_ranges(raw_spec: str) -> list[int]:
    numbers: list[int] = []
    normalized_spec = raw_spec.replace(" ", "").replace("\u060c", ",")
    for part in normalized_spec.split(","):
        if not part:
            continue
        if "-" in part:
            bounds = part.split("-", 1)
            if len(bounds) != 2:
                raise UserInputError(ar("نطاق غير صالح: ") + f"`{part}`")
            start, end = bounds
            if not start.isdigit() or not end.isdigit():
                raise UserInputError(ar("نطاق غير صالح: ") + f"`{part}`")
            start_number = int(start)
            end_number = int(end)
            if start_number <= 0 or end_number <= 0 or end_number < start_number:
                raise UserInputError(ar("نطاق غير صالح: ") + f"`{part}`")
            numbers.extend(range(start_number, end_number + 1))
        else:
            if not part.isdigit():
                raise UserInputError(ar("رقم عنصر غير صالح: ") + f"`{part}`")
            number = int(part)
            if number <= 0:
                raise UserInputError(ar("رقم عنصر غير صالح: ") + f"`{part}`")
            numbers.append(number)

    unique_numbers = sorted(set(numbers))
    if not unique_numbers:
        raise UserInputError(ar("لم يتم العثور على أرقام صالحة داخل `owned`."))
    return unique_numbers


def compress_number_ranges(numbers: list[int]) -> str:
    if not numbers:
        return ""

    sorted_numbers = sorted(set(numbers))
    ranges: list[str] = []
    start = end = sorted_numbers[0]

    for number in sorted_numbers[1:]:
        if number == end + 1:
            end = number
            continue
        ranges.append(f"{start}-{end}" if start != end else str(start))
        start = end = number

    ranges.append(f"{start}-{end}" if start != end else str(start))
    return ",".join(ranges)


def build_numeric_prompt(kind: str, initial_values: dict[str, int] | None = None) -> str:
    definition = NUMERIC_BUILDERS[kind]
    lines = [definition.intro, "", ar("القالب الجاهز:")]
    initial_values = initial_values or {}

    for field in definition.fields:
        value = initial_values.get(field.name, field.default)
        lines.append(f"{field.name}={'' if value is None else value}")

    return "\n".join(lines)


def build_inventory_prompt(
    kind: str,
    *,
    owned_numbers: list[int] | None = None,
    selected_number: int | None = None,
) -> str:
    lines = [INVENTORY_INTROS[kind], "", ar("القالب الجاهز:")]
    lines.append(f"owned={compress_number_ranges(owned_numbers or [])}")
    lines.append(f"selected={'' if selected_number is None else selected_number}")
    return "\n".join(lines)
