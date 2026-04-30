from __future__ import annotations

import json

from subway_bot.catalogs import CatalogEntry
from subway_bot.constants import DEFAULT_EVENT_COIN_EXPIRATION


def _wrap_payload(*, version: int, data: dict) -> str:
    return json.dumps(
        {
            "version": version,
            "data": json.dumps(data, separators=(",", ":")),
        },
        separators=(",", ":"),
    )


def build_wallet(values: dict[str, int]) -> str:
    payload = {
        "lastSaved": "",
        "patchVersion": 0,
        "currencies": {
            "1": {"value": values["gamecoins"]},
            "2": {"value": values["gamekeys"]},
            "3": {"value": values["hoverboards"]},
            "4": {"value": values["headstarts"]},
            "5": {"value": values["scoreboosters"]},
            "6": {
                "value": values["eventcoins"],
                "expirationValue": DEFAULT_EVENT_COIN_EXPIRATION,
                "expirationType": 1,
            },
        },
        "lootboxQueue": {"unopenedLootboxes": {"0": [], "2": []}},
        "currencyAllowedInRun": {"5": True, "4": True},
        "lootBoxesOpened": {
            "mini_mystery_box": 3,
            "mystery_box": 7,
            "token_box": 16,
            "super_mystery_box": 5,
        },
        "ownedOnlyBuyOnceProducts": ["free_token_box", "multiplier_pack", "speed_crew"],
    }
    return _wrap_payload(version=2, data=payload)


def build_badges(values: dict[str, int]) -> str:
    payload = {
        "lastSaved": "0001-01-01T00:00:00Z",
        "lastIAPDate": "0001-01-01T00:00:00Z",
        "highScoreCollection": {"default": 2147383647},
        "userStatCollection": {
            "102": values["champ"],
            "103": values["diamond"],
            "104": values["gold"],
            "105": values["silver"],
            "106": values["bronze"],
        },
    }
    return _wrap_payload(version=2, data=payload)


def build_user_stats(highscore: int) -> str:
    payload = {
        "lastSaved": "",
        "patchVersion": 0,
        "totalRuns": 0,
        "totalIAPs": 0,
        "totalIAPCurrencySpent": 0,
        "lastIAPDate": "0001-01-01T00:00:00Z",
        "lastIAPTier": 0,
        "totalTimeInRuns": 0,
        "highscore": highscore,
        "lastStoredDailyLogin": "0001-01-01T00:00:00Z",
        "numSessions": 0,
        "daysPlayed": 0,
        "lastDatePlayed": "0001-01-01T00:00:00Z",
        "prevDateLastPlayed": "0001-01-01T00:00:00Z",
    }
    return _wrap_payload(version=1, data=payload)


def build_top_run(values: dict[str, int]) -> str:
    payload = {
        "lastSaved": "",
        "patchVersion": 0,
        "hasUnclaimedReward": False,
        "currentCountry": "",
        "nextCountry": None,
        "currentScore": values["highscore"],
        "unsubmittedScore": {
            "score": values["highscore"],
            "scoreDate": "0001-01-01T00:00:00Z",
            "metadata": None,
        },
        "previousScore": 0,
        "previousBracket": None,
        "startDate": "0001-01-01T00:00:00Z",
        "lastClaimedTournamentStart": "0001-01-01T00:00:00Z",
        "friendRuns": {},
        "currentTopScoreMetadata": [
            {"key": "multiplier", "value": "1"},
            {"key": "character", "value": "jake"},
            {"key": "board", "value": "default"},
        ],
    }
    return _wrap_payload(version=1, data=payload)


def build_upgrades(values: dict[str, int]) -> str:
    payload = {
        "lastSaved": "",
        "patchVersion": 1,
        "currencyPickupModifiers": {
            "doubleCoins": {
                "value": {
                    "id": "doubleCoins",
                    "type": 0,
                    "subType": 0,
                    "value": values["doubleCoinsAmount"],
                }
            },
            "permanent_score_multiplier": {
                "value": {
                    "id": "permanent_score_multiplier",
                    "type": 2,
                    "subType": 3,
                    "value": 5,
                },
                "expirationValue": values["doubleCoinsTime"],
                "expirationType": 1,
            },
            "token_multiplier_low": {
                "value": {
                    "id": "token_multiplier_low",
                    "type": 0,
                    "subType": 2,
                    "value": values["tokenBoostAmount"],
                },
                "expirationValue": values["tokenBoostTime"],
                "expirationType": 1,
            },
        },
        "powerupLevels": {
            "jetpack": values["jetpack"],
            "superSneakers": values["superSneakers"],
            "magnet": values["magnet"],
            "doubleScore": values["doubleScore"],
        },
    }
    return _wrap_payload(version=3, data=payload)


def build_character_inventory(selected: CatalogEntry, owned: list[CatalogEntry]) -> str:
    owned_payload: dict[str, dict] = {}
    for entry in owned:
        outfits = [{"value": outfit_id} for outfit_id in (entry.extras or ("default",))]
        owned_payload[entry.id] = {"value": {"id": entry.id, "ownedOutfits": outfits}}

    payload = {
        "selected": {"character": selected.id, "outfit": "default"},
        "owned": owned_payload,
    }
    return _wrap_payload(version=3, data=payload)


def build_hoverboard_inventory(selected: CatalogEntry, owned: list[CatalogEntry]) -> str:
    owned_payload: dict[str, dict] = {}
    for entry in owned:
        upgrades = entry.extras or ("default",)
        owned_payload[entry.id] = {
            "value": {
                "id": entry.id,
                "ownedUpgrades": {upgrade_id: {"value": True} for upgrade_id in upgrades},
            }
        }

    payload = {
        "selected": selected.id,
        "owned": owned_payload,
    }
    return _wrap_payload(version=3, data=payload)


def build_profile_inventory(*, selected: CatalogEntry, owned: list[CatalogEntry]) -> str:
    owned_payload = {
        entry.id: {
            "id": entry.id,
            "isSeen": True,
        }
        for entry in owned
    }

    payload = {
        "selected": selected.id,
        "owned": owned_payload,
    }
    return _wrap_payload(version=1, data=payload)
