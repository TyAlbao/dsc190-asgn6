from datetime import date

import pytest

from nldate import parse


def test_parse_today() -> None:
    assert parse("today", today=date(2025, 12, 1)) == date(2025, 12, 1)


def test_parse_tomorrow() -> None:
    assert parse("tomorrow", today=date(2025, 12, 1)) == date(2025, 12, 2)


def test_parse_yesterday() -> None:
    assert parse("yesterday", today=date(2025, 12, 1)) == date(2025, 11, 30)


def test_parse_in_3_days() -> None:
    assert parse("in 3 days", today=date(2025, 12, 1)) == date(2025, 12, 4)


def test_parse_3_days_ago() -> None:
    assert parse("3 days ago", today=date(2025, 12, 1)) == date(2025, 11, 28)


def test_parse_next_tuesday() -> None:
    assert parse("next Tuesday", today=date(2025, 12, 1)) == date(2025, 12, 2)


def test_parse_last_friday() -> None:
    assert parse("last Friday", today=date(2025, 12, 1)) == date(2025, 11, 28)


def test_parse_december_1st_2025() -> None:
    assert parse("December 1st, 2025") == date(2025, 12, 1)


def test_parse_5_days_before_december_1st_2025() -> None:
    assert parse("5 days before December 1st, 2025") == date(2025, 11, 26)


def test_parse_2_weeks_after_december_1st_2025() -> None:
    assert parse("2 weeks after December 1st, 2025") == date(2025, 12, 15)


def test_parse_invalid_date_raises_value_error() -> None:
    with pytest.raises(ValueError):
        parse("not a real date")
