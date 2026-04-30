import json

from subway_bot.catalogs import CatalogEntry
from subway_bot.savefiles import (
    build_character_inventory,
    build_hoverboard_inventory,
    build_profile_inventory,
    build_top_run,
    build_user_stats,
    build_wallet,
)


def _unwrap(payload: str) -> dict:
    outer = json.loads(payload)
    outer["data"] = json.loads(outer["data"])
    return outer


def test_wallet_structure() -> None:
    payload = build_wallet(
        {
            "hoverboards": 1,
            "gamekeys": 2,
            "gamecoins": 3,
            "scoreboosters": 4,
            "headstarts": 5,
            "eventcoins": 6,
        }
    )
    parsed = _unwrap(payload)
    assert parsed["version"] == 2
    assert parsed["data"]["currencies"]["1"]["value"] == 3
    assert parsed["data"]["currencies"]["6"]["value"] == 6


def test_character_inventory_structure() -> None:
    selected = CatalogEntry(number=1, id="jake", name="Jake", extras=("default",))
    owned = [
        selected,
        CatalogEntry(number=2, id="tricky", name="Tricky", extras=("default", "camo")),
    ]

    parsed = _unwrap(build_character_inventory(selected, owned))
    assert parsed["data"]["selected"]["character"] == "jake"
    assert "tricky" in parsed["data"]["owned"]


def test_hoverboard_inventory_structure() -> None:
    selected = CatalogEntry(number=1, id="default", name="Default", extras=("default",))
    parsed = _unwrap(build_hoverboard_inventory(selected, [selected]))
    assert parsed["data"]["selected"] == "default"
    assert parsed["data"]["owned"]["default"]["value"]["ownedUpgrades"]["default"]["value"] is True


def test_profile_inventory_structure() -> None:
    selected = CatalogEntry(number=1, id="portrait_1", name="Portrait 1")
    parsed = _unwrap(build_profile_inventory(selected=selected, owned=[selected]))
    assert parsed["data"]["selected"] == "portrait_1"
    assert parsed["data"]["owned"]["portrait_1"]["isSeen"] is True


def test_toprun_and_user_stats_generation() -> None:
    top_run = _unwrap(build_top_run({"highscore": 99, "userstatsAmount": 77}))
    user_stats = _unwrap(build_user_stats(77))
    assert top_run["data"]["currentScore"] == 99
    assert user_stats["data"]["highscore"] == 77
