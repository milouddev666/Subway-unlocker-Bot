from __future__ import annotations

import json

from subway_bot.i18n import ar


class DocumentParseError(ValueError):
    """Raised when an uploaded save-file template cannot be parsed."""


def _load_outer_document(payload: bytes) -> dict:
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DocumentParseError(ar("الملف المرفوع ليس JSON صالحًا بترميز UTF-8.")) from exc


def _load_nested_data(document: dict) -> dict:
    raw_data = document.get("data")
    if isinstance(raw_data, str):
        try:
            return json.loads(raw_data)
        except json.JSONDecodeError as exc:
            raise DocumentParseError(ar("الحقل `data` داخل الملف ليس JSON صالحًا.")) from exc
    if isinstance(raw_data, dict):
        return raw_data
    raise DocumentParseError(ar("الملف المرفوع لا يحتوي على بنية `data` مدعومة."))


def parse_wallet_document(payload: bytes) -> dict[str, int]:
    nested = _load_nested_data(_load_outer_document(payload))
    currencies = nested.get("currencies")
    if not isinstance(currencies, dict):
        raise DocumentParseError(ar("ملف المحفظة المرفوع لا يحتوي على `currencies`."))

    currency_map = {
        "gamecoins": "1",
        "gamekeys": "2",
        "hoverboards": "3",
        "headstarts": "4",
        "scoreboosters": "5",
        "eventcoins": "6",
    }

    parsed: dict[str, int] = {}
    for field_name, currency_id in currency_map.items():
        try:
            parsed[field_name] = int(currencies[currency_id]["value"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DocumentParseError(
                ar("قيمة المحفظة التالية مفقودة أو غير صالحة: ") + f"`{field_name}`"
            ) from exc
    return parsed


def parse_character_document(payload: bytes) -> tuple[list[str], str]:
    nested = _load_nested_data(_load_outer_document(payload))
    selected = nested.get("selected")
    owned = nested.get("owned")

    if not isinstance(selected, dict) or not isinstance(owned, dict):
        raise DocumentParseError(ar("ملف الشخصيات المرفوع يفتقد `selected` أو `owned`."))

    character_id = selected.get("character")
    if not isinstance(character_id, str):
        raise DocumentParseError(ar("قيمة الشخصية المحددة داخل الملف غير صالحة."))

    owned_ids = list(owned.keys())
    if not owned_ids:
        raise DocumentParseError(ar("ملف الشخصيات المرفوع فارغ."))

    return owned_ids, character_id


def parse_hoverboard_document(payload: bytes) -> tuple[list[str], str]:
    nested = _load_nested_data(_load_outer_document(payload))
    selected = nested.get("selected")
    owned = nested.get("owned")

    if not isinstance(selected, str) or not isinstance(owned, dict):
        raise DocumentParseError(ar("ملف الألواح المرفوع يفتقد `selected` أو `owned`."))

    owned_ids = list(owned.keys())
    if not owned_ids:
        raise DocumentParseError(ar("ملف الألواح المرفوع فارغ."))

    return owned_ids, selected
