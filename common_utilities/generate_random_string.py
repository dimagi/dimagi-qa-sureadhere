import random
import string
import time

"""Generates random values for test data across CCHQ"""

CHARS = string.ascii_lowercase + string.digits
PHONE_DIGITS = 10


def fetch_random_string(length: int = 6) -> str:
    """Generate a new random string on every call."""
    return ''.join(random.choices(CHARS, k=length))


def fetch_random_string_unique(length: int = 4) -> str:
    """
    Strongly unique random string.
    Safe for parallel runs, reruns, and fast consecutive calls.
    """
    ts = int(time.time() * 1000)  # milliseconds
    rand = ''.join(random.choices(string.ascii_lowercase, k=length))
    return f"{rand}{ts}"


def fetch_phone_number() -> str:
    min_value = 10 ** (PHONE_DIGITS - 1)
    max_value = (10 ** PHONE_DIGITS) - 1
    return str(random.randint(min_value, max_value))


def fetch_random_digit(start: int = 100, end: int = 19999) -> str:
    return str(random.randint(start, end))


def fetch_random_boolean() -> bool:
    return random.choice([True, False])


def fetch_random_digit_with_range(start: int, end: int) -> str:
    return str(random.randint(start, end))


def fetch_string_with_special_chars(length: int) -> str:
    return ''.join(
        random.choices(
            string.ascii_lowercase + string.digits + string.punctuation,
            k=length
        )
    )
