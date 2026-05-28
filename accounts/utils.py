"""
accounts/utils.py — Utility helpers for the Accounts app.
"""
from __future__ import annotations

import re
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. National ID / Passport validators
# ---------------------------------------------------------------------------

_NATIONAL_ID_RE = re.compile(r'^\d{9}$')
_PASSPORT_RE    = re.compile(r'^[A-Z]{2}\d{7}$')


def validate_national_id(value: str) -> bool:
    """Return ``True`` if *value* is a valid 9-digit Armenian national ID."""
    return bool(_NATIONAL_ID_RE.match(str(value).strip()))


def validate_passport(value: str) -> bool:
    """Return ``True`` if *value* matches the Armenian passport format (AA1234567)."""
    return bool(_PASSPORT_RE.match(str(value).strip().upper()))


def validate_document(doc_type: str, value: str) -> tuple[bool, str]:
    """
    Validate a document number given its type.

    Returns ``(is_valid, error_message)``; *error_message* is empty string
    when *is_valid* is ``True``.
    """
    value = value.strip()
    if doc_type == "national_id_card":
        if validate_national_id(value):
            return True, ""
        return False, "National ID must be exactly 9 digits."
    if doc_type == "passport":
        if validate_passport(value.upper()):
            return True, ""
        return False, "Passport must be 2 uppercase letters followed by 7 digits (e.g. AB1234567)."
    return False, f"Unknown document type: {doc_type!r}"


# ---------------------------------------------------------------------------
# 2. Phone number normaliser
# ---------------------------------------------------------------------------

_PHONE_RE = re.compile(r'^\+374-\d{2}-\d{6}$')


def normalise_phone(raw: str) -> str:
    """
    Strip whitespace and normalise a phone number to +374-XX-XXXXXX format.

    Returns the normalised string, or the original input if it cannot be parsed.
    """
    raw = raw.strip().replace(' ', '').replace('(', '').replace(')', '')
    # Already in canonical form
    if _PHONE_RE.match(raw):
        return raw
    # Strip leading country code variants (00374, +374, 374)
    digits = re.sub(r'\D', '', raw)
    if digits.startswith('374'):
        digits = digits[3:]
    if len(digits) == 8:
        return f'+374-{digits[:2]}-{digits[2:]}'
    return raw  # cannot normalise — return as-is


def is_valid_phone(phone: str) -> bool:
    """Return ``True`` if *phone* matches the canonical Armenian mobile format."""
    return bool(_PHONE_RE.match(phone.strip()))


# ---------------------------------------------------------------------------
# 3. User display helpers
# ---------------------------------------------------------------------------

def get_display_name(user: "User") -> str:
    """Return the best human-readable name for *user*."""
    full = user.get_full_name().strip()
    return full or user.username


def get_initials(user: "User") -> str:
    """Return up to two uppercase initials for avatar placeholder rendering."""
    first = (user.first_name or '').strip()
    last  = (user.last_name  or '').strip()
    if first and last:
        return (first[0] + last[0]).upper()
    if first:
        return first[:2].upper()
    return user.username[:2].upper()


def get_role_badge(user: "User") -> dict:
    """
    Return CSS token dict for the user's role badge.

    Example return value::

        {'label': 'Admin', 'bg': '#EEF2FF', 'color': '#4338CA', 'border': '#C7D2FE'}
    """
    if user.is_admin_user:
        return {'label': 'Admin', 'bg': '#EEF2FF', 'color': '#4338CA', 'border': '#C7D2FE'}
    if user.verified:
        return {'label': 'Verified', 'bg': '#DCFCE7', 'color': '#14532D', 'border': '#BBF7D0'}
    return {'label': 'Citizen', 'bg': '#F1F5F9', 'color': '#334155', 'border': '#E2E8F0'}


# ---------------------------------------------------------------------------
# 4. Anonymisation helper (GDPR / data deletion support)
# ---------------------------------------------------------------------------

def anonymise_user(user: "User") -> None:
    """
    Replace all personal data on *user* with anonymised placeholders.

    This does **not** delete the row — doing so would break foreign-key
    references from issues, votes, comments, etc.  Callers are responsible
    for saving and for any additional cleanup.
    """
    uid = user.pk
    user.username    = f"deleted_user_{uid}"
    user.first_name  = ""
    user.last_name   = ""
    user.email       = f"deleted_{uid}@invalid.example"
    user.phone       = ""
    user.address     = ""
    user.national_id = None
    user.avatar      = None
    user.is_active   = False
    logger.info("User #%s anonymised.", uid)
