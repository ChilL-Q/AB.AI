import re


def normalize_phone(phone: str) -> str:
    """Normalize phone to +7XXXXXXXXXX (Kazakhstan/Russia) or generic +XXXXXXX format."""
    digits = re.sub(r"\D", "", phone)

    # KZ/RU: 8XXXXXXXXXX → +7XXXXXXXXXX
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]

    if not digits.startswith("+"):
        digits = "+" + digits

    return digits
