from telegram import BotCommand

from subway_bot.i18n import ar

MAX_SIGNED_32 = 2_147_483_647
MAX_SIGNED_63 = 9_223_372_036_854_775_807
DEFAULT_UPGRADE_EXPIRATION = 999_999_999_999_999
DEFAULT_EVENT_COIN_EXPIRATION = 99_999_999_999_999
DEFAULT_CATALOG_PAGE_SIZE = 20

RELEASE_BASE_URL = "https://github.com/HerrErde/subway-source/releases/latest/download"

SUPPORTED_EDITABLE_DOCUMENTS = {
    "wallet.json": "wallet",
    "characters_inventory.json": "characters",
    "boards_inventory.json": "hoverboards",
}

CATALOG_KIND_ALIASES = {
    "character": "characters",
    "characters": "characters",
    ar("ط´ط®طµظٹط§طھ"): "characters",
    ar("ط§ظ„ط´ط®طµظٹط§طھ"): "characters",
    "board": "hoverboards",
    "boards": "hoverboards",
    "hoverboard": "hoverboards",
    "hoverboards": "hoverboards",
    ar("ط§ظ„ظˆط§ط­"): "hoverboards",
    ar("ط£ظ„ظˆط§ط­"): "hoverboards",
    ar("ط§ظ„ظˆط§ط­ ط§ظ„طھط²ظ„ط¬"): "hoverboards",
    ar("ط£ظ„ظˆط§ط­ ط§ظ„طھط²ظ„ط¬"): "hoverboards",
    "portrait": "portraits",
    "portraits": "portraits",
    ar("طµظˆط±"): "portraits",
    ar("ط§ظ„طµظˆط±"): "portraits",
    ar("ط§ظ„طµظˆط± ط§ظ„ط´ط®طµظٹط©"): "portraits",
    "frame": "frames",
    "frames": "frames",
    ar("ط¥ط·ط§ط±ط§طھ"): "frames",
    ar("ط§ظ„ط§ط·ط§ط±ط§طھ"): "frames",
    ar("ط§ظ„ط¥ط·ط§ط±ط§طھ"): "frames",
}

CATALOG_ENDPOINTS = {
    "characters": {
        "data": f"{RELEASE_BASE_URL}/characters_data.json",
        "links": f"{RELEASE_BASE_URL}/characters_links.json",
    },
    "hoverboards": {
        "data": f"{RELEASE_BASE_URL}/boards_data.json",
        "links": f"{RELEASE_BASE_URL}/boards_links.json",
    },
    "playerprofile": {
        "data": f"{RELEASE_BASE_URL}/playerprofile_data.json",
        "links": f"{RELEASE_BASE_URL}/playerprofile_links.json",
    },
}

BOT_COMMANDS = [
    BotCommand("start", ar("ط§ظ„ظˆط§ط¬ظ‡ط© ط§ظ„ط±ط¦ظٹط³ظٹط©")),
    BotCommand("menu", ar("ط¹ط±ط¶ ط§ظ„ظ‚ط§ط¦ظ…ط© ط§ظ„ط±ط¦ظٹط³ظٹط©")),
    BotCommand("help", ar("ط´ط±ط­ ط§ظ„ط§ط³طھط®ط¯ط§ظ…")),
    BotCommand("catalog", ar("ط¹ط±ط¶ ظپظ‡ط±ط³ ط§ظ„ط¹ظ†ط§طµط± ط¨ط§ظ„ط£ط±ظ‚ط§ظ…")),
    BotCommand("wallet", ar("ط¥ظ†ط´ط§ط، ظ…ظ„ظپ ط§ظ„ظ…ط­ظپط¸ط©")),
    BotCommand("characters", ar("ط¥ظ†ط´ط§ط، ظ…ظ„ظپ ط§ظ„ط´ط®طµظٹط§طھ")),
    BotCommand("characters_all", ar("ظپطھط­ ظƒظ„ ط§ظ„ط´ط®طµظٹط§طھ ظ…ط¨ط§ط´ط±ط©")),
    BotCommand("hoverboards", ar("ط¥ظ†ط´ط§ط، ظ…ظ„ظپ ط£ظ„ظˆط§ط­ ط§ظ„طھط²ظ„ط¬")),
    BotCommand("hoverboards_all", ar("ظپطھط­ ظƒظ„ ط£ظ„ظˆط§ط­ ط§ظ„طھط²ظ„ط¬ ظ…ط¨ط§ط´ط±ط©")),
    BotCommand("portraits", ar("ط¥ظ†ط´ط§ط، ظ…ظ„ظپ ط§ظ„طµظˆط± ط§ظ„ط´ط®طµظٹط©")),
    BotCommand("frames", ar("ط¥ظ†ط´ط§ط، ظ…ظ„ظپ ط§ظ„ط¥ط·ط§ط±ط§طھ")),
    BotCommand("badges", ar("ط¥ظ†ط´ط§ط، ظ…ظ„ظپ ط§ظ„ط´ط§ط±ط§طھ")),
    BotCommand("upgrades", ar("ط¥ظ†ط´ط§ط، ظ…ظ„ظپ ط§ظ„طھط·ظˆظٹط±ط§طھ")),
    BotCommand("toprun", ar("ط¥ظ†ط´ط§ط، ظ…ظ„ظپ ط£ط¹ظ„ظ‰ ظ†طھظٹط¬ط©")),
    BotCommand("cancel", ar("ط¥ظ„ط؛ط§ط، ط§ظ„ط¹ظ…ظ„ظٹط© ط§ظ„ط­ط§ظ„ظٹط©")),
]
