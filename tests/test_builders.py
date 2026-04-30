from subway_bot.builders import (
    UserInputError,
    compress_number_ranges,
    expand_number_ranges,
    parse_inventory_input,
    parse_numeric_input,
)


def test_parse_wallet_input() -> None:
    values = parse_numeric_input(
        "wallet",
        "\n".join(
            [
                "hoverboards=10",
                "gamekeys=20",
                "gamecoins=30",
                "scoreboosters=40",
                "headstarts=50",
                "eventcoins=60",
            ]
        ),
    )

    assert values["hoverboards"] == 10
    assert values["eventcoins"] == 60


def test_toprun_defaults_user_stats_to_highscore() -> None:
    values = parse_numeric_input("toprun", "highscore=1234")
    assert values == {"highscore": 1234, "userstatsAmount": 1234}


def test_inventory_input_parses_ranges() -> None:
    payload = parse_inventory_input("owned=1-3,8\nselected=2")
    assert payload.owned_spec == "1-3,8"
    assert payload.selected == 2
    assert expand_number_ranges(payload.owned_spec) == [1, 2, 3, 8]


def test_inventory_input_accepts_arabic_comma() -> None:
    assert expand_number_ranges("1-3،8") == [1, 2, 3, 8]


def test_range_compression_round_trips() -> None:
    numbers = [1, 2, 3, 5, 8, 9]
    assert compress_number_ranges(numbers) == "1-3,5,8-9"


def test_invalid_range_raises() -> None:
    try:
        expand_number_ranges("4-1")
    except UserInputError:
        return
    raise AssertionError("Expected UserInputError for a descending range.")
