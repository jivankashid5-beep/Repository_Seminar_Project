"""Helper functions for converting and formatting bill values."""

import re
from datetime import date as date_type, datetime

from num2words import num2words

# Common English and Hindi number words written using the English alphabet.
_NUMBER_WORDS = {
    "zero": 0,
    "shunya": 0,
    "one": 1,
    "a": 1,
    "an": 1,
    "ek": 1,
    "two": 2,
    "do": 2,
    "three": 3,
    "teen": 3,
    "four": 4,
    "char": 4,
    "chaar": 4,
    "five": 5,
    "paanch": 5,
    "panch": 5,
    "six": 6,
    "chhe": 6,
    "chhah": 6,
    "seven": 7,
    "saat": 7,
    "eight": 8,
    "aath": 8,
    "nine": 9,
    "nau": 9,
    "ten": 10,
    "das": 10,
    "eleven": 11,
    "gyarah": 11,
    "twelve": 12,
    "barah": 12,
    "thirteen": 13,
    "terah": 13,
    "fourteen": 14,
    "chaudah": 14,
    "fifteen": 15,
    "pandrah": 15,
    "sixteen": 16,
    "solah": 16,
    "seventeen": 17,
    "satrah": 17,
    "eighteen": 18,
    "atharah": 18,
    "nineteen": 19,
    "unnis": 19,
    "twenty": 20,
    "bees": 20,
    "ikkis": 21,
    "bais": 22,
    "teis": 23,
    "chaubis": 24,
    "pachis": 25,
    "chhabbees": 26,
    "sattais": 27,
    "athais": 28,
    "untis": 29,
    "thirty": 30,
    "tees": 30,
    "ikattis": 31,
    "forty": 40,
    "chalis": 40,
    "fifty": 50,
    "pachas": 50,
    "sixty": 60,
    "saath": 60,
    "seventy": 70,
    "sattar": 70,
    "eighty": 80,
    "assi": 80,
    "ninety": 90,
    "nabbe": 90,
}

_MULTIPLIERS = {
    "hundred": 100,
    "sau": 100,
    "thousand": 1_000,
    "hazaar": 1_000,
    "hazar": 1_000,
    "lakh": 100_000,
    "lac": 100_000,
    "crore": 10_000_000,
}

# Hindi number words in Devanagari, commonly returned for hi-IN speech input.
_HINDI_WORDS = {
    "शून्य": "zero",
    "एक": "ek",
    "दो": "do",
    "तीन": "teen",
    "चार": "chaar",
    "पांच": "paanch",
    "पाँच": "paanch",
    "छह": "chhe",
    "छः": "chhe",
    "सात": "saat",
    "आठ": "aath",
    "नौ": "nau",
    "दस": "das",
    "ग्यारह": "gyarah",
    "बारह": "barah",
    "तेरह": "terah",
    "चौदह": "chaudah",
    "पंद्रह": "pandrah",
    "पन्द्रह": "pandrah",
    "सोलह": "solah",
    "सत्रह": "satrah",
    "अठारह": "atharah",
    "उन्नीस": "unnis",
    "बीस": "bees",
    "इक्कीस": "ikkis",
    "बाईस": "bais",
    "बाइस": "bais",
    "तेईस": "teis",
    "चौबीस": "chaubis",
    "पच्चीस": "pachis",
    "छब्बीस": "chhabbees",
    "सत्ताईस": "sattais",
    "अट्ठाईस": "athais",
    "उनतीस": "untis",
    "तीस": "tees",
    "इकतीस": "ikattis",
    "चालीस": "chalis",
    "पचास": "pachas",
    "साठ": "saath",
    "सत्तर": "sattar",
    "अस्सी": "assi",
    "नब्बे": "nabbe",
    "सौ": "sau",
    "हज़ार": "hazaar",
    "हजार": "hazaar",
    "लाख": "lakh",
    "करोड़": "crore",
    "करोड": "crore",
}


def words_to_number(text):
    """Convert common English/Hindi number words or digits to an integer."""
    text = text.lower().strip().replace(",", "")
    if not text:
        raise ValueError("Please provide a number.")

    # Handle a number entered directly, such as "2200".
    if text.isdigit():
        return int(text)

    total = 0
    current = 0
    found_number_word = False

    # Split on spaces and hyphens so "twenty-five" becomes two words.
    tokens = re.findall(r"[\u0900-\u097F]+|[a-z]+|\d+", text)
    for word in tokens:
        # Translate a whole Hindi word, avoiding accidental partial matches.
        word = _HINDI_WORDS.get(word, word)
        if word == "and":
            continue
        if word in _NUMBER_WORDS:
            found_number_word = True
            current += _NUMBER_WORDS[word]
        elif word.isdigit():
            found_number_word = True
            current += int(word)
        elif word in _MULTIPLIERS:
            found_number_word = True
            multiplier = _MULTIPLIERS[word]
            if multiplier == 100:
                current = max(current, 1) * multiplier
            else:
                total += max(current, 1) * multiplier
                current = 0
        else:
            raise ValueError(f"Unknown number word: {word}")

    if not found_number_word:
        raise ValueError("No number was recognized.")
    return total + current


def amount_in_words(n):
    """Return an amount in Indian-style English words, ending with 'Only'."""
    words = num2words(n, lang="en_IN").replace(",", "").title()
    return f"{words} Only"


def calculate_total(rows):
    """Add the numeric 'amount' value from each bill-row dictionary."""
    return sum(row["amount"] for row in rows)


def format_date(date):
    """Format a date as DD.MM.YY (accepts date objects and common date strings)."""
    if isinstance(date, datetime):
        parsed_date = date.date()
    elif isinstance(date, date_type):
        parsed_date = date
    else:
        accepted_formats = (
            "%Y-%m-%d",
            "%d.%m.%Y",
            "%d.%m.%y",
            "%d/%m/%Y",
            "%d/%m/%y",
            "%d-%m-%Y",
            "%d-%m-%y",
        )
        parsed_date = None
        for date_format in accepted_formats:
            try:
                parsed_date = datetime.strptime(date, date_format).date()
                break
            except ValueError:
                continue

        if parsed_date is None:
            raise ValueError("Date must use YYYY-MM-DD or DD/MM/YYYY format.")

    return parsed_date.strftime("%d.%m.%y")


if __name__ == "__main__":
    # Run these simple checks with: python parser.py
    assert words_to_number("do hazaar do sau") == 2200
    assert words_to_number("two thousand") == 2000
    assert words_to_number("2200") == 2200
    assert words_to_number("one hundred and twenty-five") == 125
    assert words_to_number("दो हजार दो सौ") == 2200
    assert amount_in_words(2200) == "Two Thousand Two Hundred Only"
    assert calculate_total([{"amount": 100}, {"amount": 250}]) == 350
    assert calculate_total([]) == 0
    assert format_date("2026-09-05") == "05.09.26"
    assert format_date("05.09.26") == "05.09.26"
    assert format_date(date_type(2026, 9, 5)) == "05.09.26"

    print("All 11 parser tests passed.")
