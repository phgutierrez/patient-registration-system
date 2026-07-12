import re
import secrets

PIN_PATTERN = re.compile(r"^\d{6}$")
PIN_MESSAGE = "A senha deve conter exatamente 6 dígitos."


def is_valid_pin(value: str) -> bool:
    return bool(PIN_PATTERN.fullmatch(value or ""))


def generate_pin() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"
