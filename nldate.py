from __future__ import annotations

import calendar
import re
from datetime import date, timedelta


_MONTH_NAMES = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

_WEEKDAYS = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}

_NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}

_SCALE_WORDS = {
    "hundred": 100,
    "thousand": 1000,
}

_UNIT_ALIASES = {
    "day": "days",
    "days": "days",
    "week": "weeks",
    "weeks": "weeks",
    "month": "months",
    "months": "months",
    "year": "years",
    "years": "years",
}

_DIRECT_RELATIVE_DAYS = {
    "today": 0,
    "now": 0,
    "tomorrow": 1,
    "yesterday": -1,
    "day after tomorrow": 2,
    "day before yesterday": -2,
}


def parse(s: str, today: date | None = None) -> date:
    reference = today if today is not None else date.today()
    text = _normalize_text(s)
    if not text:
        raise ValueError("empty date expression")
    return _parse_expression(text, reference)


def _parse_expression(text: str, today: date) -> date:
    if text in _DIRECT_RELATIVE_DAYS:
        return today + timedelta(days=_DIRECT_RELATIVE_DAYS[text])

    if result := _parse_weekday_reference(text, today):
        return result

    if result := _parse_simple_relative(text, today):
        return result

    compound_match = re.fullmatch(r"(.+?)\s+(before|after|from)\s+(.+)", text)
    if compound_match:
        duration_text, relation, base_text = compound_match.groups()
        duration = _parse_duration(duration_text)
        base_date = _parse_expression(base_text, today)
        if relation == "before":
            return _add_duration(base_date, duration, sign=-1)
        return _add_duration(base_date, duration, sign=1)

    if result := _parse_absolute_date(text, today):
        return result

    raise ValueError(f"could not parse date expression: {text!r}")


def _normalize_text(text: str) -> str:
    normalized = text.strip().lower()
    normalized = normalized.replace("’", "'")
    normalized = re.sub(r"^[\s,]+|[\s,]+$", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    if normalized.startswith("on "):
        normalized = normalized[3:]
    if normalized.startswith("the "):
        normalized = normalized[4:]
    return normalized


def _parse_weekday_reference(text: str, today: date) -> date | None:
    match = re.fullmatch(r"(next|last|this)\s+([a-z.]+)", text)
    if not match:
        return None

    direction, weekday_text = match.groups()
    weekday = _lookup_weekday(weekday_text)
    if weekday is None:
        return None

    current = today.weekday()
    if direction == "this":
        offset = weekday - current
    elif direction == "next":
        offset = (weekday - current) % 7
        if offset == 0:
            offset = 7
    else:
        offset = -((current - weekday) % 7)
        if offset == 0:
            offset = -7

    return today + timedelta(days=offset)


def _parse_simple_relative(text: str, today: date) -> date | None:
    if match := re.fullmatch(r"in (.+)", text):
        return _add_duration(today, _parse_duration(match.group(1)))

    if match := re.fullmatch(r"(.+?) ago", text):
        return _add_duration(today, _parse_duration(match.group(1)), sign=-1)

    if match := re.fullmatch(r"(.+?) (?:from now|later|hence)", text):
        return _add_duration(today, _parse_duration(match.group(1)))

    return None


def _parse_absolute_date(text: str, today: date) -> date | None:
    cleaned = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", text)

    if re.fullmatch(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", cleaned):
        year_text, month_text, day_text = re.split(r"[-/]", cleaned)
        return date(int(year_text), int(month_text), int(day_text))

    if match := re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", cleaned):
        month, day, year = (int(part) for part in match.groups())
        return date(year, month, day)

    if match := re.fullmatch(r"(\d{1,2})/(\d{1,2})", cleaned):
        month, day = (int(part) for part in match.groups())
        return date(today.year, month, day)

    if parsed := _parse_month_name_date(cleaned, today.year):
        return parsed

    return None


def _parse_month_name_date(text: str, default_year: int) -> date | None:
    patterns = (
        r"([a-z.]+) (\d{1,2})(?:, (\d{4}))?",
        r"(\d{1,2}) ([a-z.]+)(?: (\d{4}))?",
    )

    for pattern in patterns:
        match = re.fullmatch(pattern, text)
        if not match:
            continue

        first, second, year_text = match.groups()
        if first.isdigit():
            day = int(first)
            month = _lookup_month(second)
        else:
            month = _lookup_month(first)
            day = int(second)

        if month is None:
            return None

        year = default_year if year_text is None else int(year_text)
        return date(year, month, day)

    return None


def _parse_duration(text: str) -> dict[str, int]:
    cleaned = text.replace(",", " ")
    tokens = [token for token in cleaned.split() if token]
    if not tokens:
        raise ValueError("empty duration")

    duration = {"days": 0, "weeks": 0, "months": 0, "years": 0}
    index = 0

    while index < len(tokens):
        next_unit_index = _find_next_unit_index(tokens, index)
        if next_unit_index is None:
            raise ValueError(f"invalid duration: {text!r}")

        quantity_tokens = tokens[index:next_unit_index]
        quantity = _parse_number_tokens(quantity_tokens)
        unit = _UNIT_ALIASES[tokens[next_unit_index]]
        duration[unit] += quantity
        index = next_unit_index + 1

        while index < len(tokens) and tokens[index] == "and":
            index += 1

    return duration


def _find_next_unit_index(tokens: list[str], start: int) -> int | None:
    for index in range(start + 1, len(tokens)):
        if tokens[index] in _UNIT_ALIASES:
            return index
    return None


def _parse_number_tokens(tokens: list[str]) -> int:
    if not tokens:
        raise ValueError("missing quantity")

    joined = " ".join(tokens)
    if joined.isdigit():
        return int(joined)

    normalized_tokens: list[str] = []
    for token in tokens:
        for part in token.replace("-", " ").split():
            if part:
                normalized_tokens.append(part)

    if not normalized_tokens:
        raise ValueError("missing quantity")

    if len(normalized_tokens) == 1 and normalized_tokens[0] in {"a", "an"}:
        return 1

    total = 0
    current = 0
    seen_number = False

    for token in normalized_tokens:
        if token == "and":
            continue
        if token in {"a", "an"}:
            current += 1
            seen_number = True
            continue
        if token in _NUMBER_WORDS:
            current += _NUMBER_WORDS[token]
            seen_number = True
            continue
        if token in _SCALE_WORDS:
            if current == 0:
                current = 1
            current *= _SCALE_WORDS[token]
            if _SCALE_WORDS[token] >= 1000:
                total += current
                current = 0
            seen_number = True
            continue
        raise ValueError(f"invalid quantity: {joined!r}")

    if not seen_number:
        raise ValueError(f"invalid quantity: {joined!r}")
    return total + current


def _lookup_month(token: str) -> int | None:
    return _MONTH_NAMES.get(token.rstrip("."))


def _lookup_weekday(token: str) -> int | None:
    return _WEEKDAYS.get(token.rstrip("."))


def _add_duration(base: date, duration: dict[str, int], sign: int = 1) -> date:
    shifted = _add_months(base, sign * (duration["years"] * 12 + duration["months"]))
    shifted += timedelta(days=sign * (duration["weeks"] * 7 + duration["days"]))
    return shifted


def _add_months(base: date, months: int) -> date:
    if months == 0:
        return base

    month_index = (base.month - 1) + months
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    day = min(base.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)
