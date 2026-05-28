"""
accounts/validators.py — Field validators for the Accounts app.
"""
from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# ---------------------------------------------------------------------------
# 1. National ID / Passport validators (model-level)
# ---------------------------------------------------------------------------

_NATIONAL_ID_RE = re.compile(r'^\d{9}$')
_PASSPORT_RE    = re.compile(r'^[A-Z]{2}\d{7}$')


def validate_national_id_format(value: str) -> None:
    """
    Accept either a 9-digit national ID card number OR a passport number
    (2 uppercase letters + 7 digits).

    The actual format depends on the ``doc_type`` field, but this validator
    accepts both so that the model-level unique constraint works regardless.
    """
    v = str(value).strip().upper()
    if _NATIONAL_ID_RE.match(v) or _PASSPORT_RE.match(v):
        return
    raise ValidationError(
        _("Enter a valid 9-digit national ID (e.g. 123456789) "
          "or a passport number (e.g. AB1234567).")
    )


# ---------------------------------------------------------------------------
# 2. Phone number validator
# ---------------------------------------------------------------------------

_PHONE_RE = re.compile(r'^\+374-\d{2}-\d{6}$')


def validate_armenian_phone(value: str) -> None:
    """
    Validate Armenian mobile phone number in +374-XX-XXXXXX format.
    An empty string is allowed (phone is optional).
    """
    if not value:
        return
    if not _PHONE_RE.match(value.strip()):
        raise ValidationError(
            _("Enter a phone number in +374-XX-XXXXXX format (e.g. +374-77-123456).")
        )


# ---------------------------------------------------------------------------
# 3. Username validator
# ---------------------------------------------------------------------------

_USERNAME_RE = re.compile(r'^[\w.@+-]+$')
MIN_USERNAME_LEN = 3
MAX_USERNAME_LEN = 30


def validate_username_format(value: str) -> None:
    """
    Enforce Kapantsi username rules:
    - 3–30 characters
    - alphanumeric plus . @ + - _ only
    - not all-numeric
    """
    v = str(value).strip()
    if len(v) < MIN_USERNAME_LEN:
        raise ValidationError(
            _("Username must be at least %(min)d characters."),
            params={"min": MIN_USERNAME_LEN},
        )
    if len(v) > MAX_USERNAME_LEN:
        raise ValidationError(
            _("Username must not exceed %(max)d characters."),
            params={"max": MAX_USERNAME_LEN},
        )
    if not _USERNAME_RE.match(v):
        raise ValidationError(
            _("Username may only contain letters, digits, and . @ + - _ characters.")
        )
    if v.isdigit():
        raise ValidationError(_("Username cannot consist entirely of digits."))


# ---------------------------------------------------------------------------
# 4. Password strength validator (used via AUTH_PASSWORD_VALIDATORS)
# ---------------------------------------------------------------------------

class KapantsiPasswordValidator:
    """
    Custom password validator:
    - At least 8 characters
    - Contains at least one digit
    - Contains at least one letter
    """

    def validate(self, password: str, user=None) -> None:
        if len(password) < 8:
            raise ValidationError(
                _("Password must be at least 8 characters long."),
                code="password_too_short",
            )
        if not any(c.isdigit() for c in password):
            raise ValidationError(
                _("Password must contain at least one digit."),
                code="password_no_digit",
            )
        if not any(c.isalpha() for c in password):
            raise ValidationError(
                _("Password must contain at least one letter."),
                code="password_no_letter",
            )

    def get_help_text(self) -> str:
        return _(
            "Your password must be at least 8 characters long and contain "
            "at least one letter and one digit."
        )


# ---------------------------------------------------------------------------
# 5. Address / location validator
# ---------------------------------------------------------------------------

MIN_ADDRESS_LEN = 5
MAX_ADDRESS_LEN = 255


def validate_address(value: str) -> None:
    """Basic sanity check on a free-text address field."""
    if not value:
        return
    stripped = value.strip()
    if len(stripped) < MIN_ADDRESS_LEN:
        raise ValidationError(
            _("Address must be at least %(min)d characters."),
            params={"min": MIN_ADDRESS_LEN},
        )
    if len(stripped) > MAX_ADDRESS_LEN:
        raise ValidationError(
            _("Address must not exceed %(max)d characters."),
            params={"max": MAX_ADDRESS_LEN},
        )
