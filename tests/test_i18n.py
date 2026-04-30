from subway_bot.i18n import ar


def test_ar_decodes_mojibake_arabic() -> None:
    assert ar("ط§ظ„ظˆط§ط¬ظ‡ط©") == "\u0627\u0644\u0648\u0627\u062c\u0647\u0629"


def test_ar_decodes_double_mojibake_arabic() -> None:
    assert ar("ط·آ§ط¸â€‍ط¸ث†ط·آ§ط·آ¬ط¸â€،ط·آ©") == "\u0627\u0644\u0648\u0627\u062c\u0647\u0629"
