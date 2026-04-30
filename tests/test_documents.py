import json

from subway_bot.documents import (
    parse_character_document,
    parse_hoverboard_document,
    parse_wallet_document,
)


def test_parse_wallet_document() -> None:
    payload = json.dumps(
        {
            "version": 2,
            "data": json.dumps(
                {
                    "currencies": {
                        "1": {"value": 111},
                        "2": {"value": 222},
                        "3": {"value": 333},
                        "4": {"value": 444},
                        "5": {"value": 555},
                        "6": {"value": 666},
                    }
                }
            ),
        }
    ).encode("utf-8")

    values = parse_wallet_document(payload)
    assert values == {
        "gamecoins": 111,
        "gamekeys": 222,
        "hoverboards": 333,
        "headstarts": 444,
        "scoreboosters": 555,
        "eventcoins": 666,
    }


def test_parse_character_document() -> None:
    payload = json.dumps(
        {
            "version": 3,
            "data": json.dumps(
                {
                    "selected": {"character": "jake", "outfit": "default"},
                    "owned": {
                        "jake": {"value": {"id": "jake", "ownedOutfits": [{"value": "default"}]}},
                        "tricky": {
                            "value": {
                                "id": "tricky",
                                "ownedOutfits": [{"value": "default"}],
                            }
                        },
                    },
                }
            ),
        }
    ).encode("utf-8")

    owned_ids, selected_id = parse_character_document(payload)
    assert owned_ids == ["jake", "tricky"]
    assert selected_id == "jake"


def test_parse_hoverboard_document() -> None:
    payload = json.dumps(
        {
            "version": 3,
            "data": json.dumps(
                {
                    "selected": "default",
                    "owned": {
                        "default": {
                            "value": {
                                "id": "default",
                                "ownedUpgrades": {"default": {"value": True}},
                            }
                        }
                    },
                }
            ),
        }
    ).encode("utf-8")

    owned_ids, selected_id = parse_hoverboard_document(payload)
    assert owned_ids == ["default"]
    assert selected_id == "default"
