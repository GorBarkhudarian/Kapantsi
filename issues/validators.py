"""
issues/validators.py — Django / DRF field validators for the Issues app.

These validators are imported into model fields and serializers via
``validators=[…]`` lists and also used directly in forms.
"""
from __future__ import annotations

import re
from typing import Any

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# ---------------------------------------------------------------------------
# 1. Title validators
# ---------------------------------------------------------------------------

MIN_TITLE_LENGTH = 10
MAX_TITLE_LENGTH = 200


def validate_title_not_empty(value: str) -> None:
    """Reject blank or whitespace-only titles."""
    if not value or not value.strip():
        raise ValidationError(_("Title cannot be blank."))


def validate_title_length(value: str) -> None:
    """Enforce minimum and maximum title lengths."""
    stripped = value.strip()
    if len(stripped) < MIN_TITLE_LENGTH:
        raise ValidationError(
            _("Title must be at least %(min)d characters long."),
            params={"min": MIN_TITLE_LENGTH},
        )
    if len(stripped) > MAX_TITLE_LENGTH:
        raise ValidationError(
            _("Title must not exceed %(max)d characters."),
            params={"max": MAX_TITLE_LENGTH},
        )


def validate_title_no_spam(value: str) -> None:
    """
    Reject titles that look like spam (all caps, repeated chars, etc.).
    """
    stripped = value.strip()
    # All-uppercase with at least 5 characters
    if len(stripped) >= 5 and stripped == stripped.upper() and stripped.replace(' ', '').isalpha():
        raise ValidationError(_("Please do not write the title in ALL CAPS."))
    # Repeated single character (e.g. "aaaaaaa")
    if re.match(r'^(.)\1{9,}$', stripped.replace(' ', '')):
        raise ValidationError(_("Title appears to contain repeated characters."))


# ---------------------------------------------------------------------------
# 2. Description / body validators
# ---------------------------------------------------------------------------

MIN_DESCRIPTION_LENGTH = 20


def validate_description_length(value: str) -> None:
    """Enforce a minimum description length."""
    if value and len(value.strip()) < MIN_DESCRIPTION_LENGTH:
        raise ValidationError(
            _("Description must be at least %(min)d characters long."),
            params={"min": MIN_DESCRIPTION_LENGTH},
        )


# ---------------------------------------------------------------------------
# 3. Coordinate validators
# ---------------------------------------------------------------------------

# Bounding box for the Kapan / Syunik region (with some margin)
LAT_MIN, LAT_MAX = 38.8, 39.8
LNG_MIN, LNG_MAX = 46.0, 46.8


def validate_latitude(value: Any) -> None:
    """Check that *value* is a valid WGS-84 latitude within Kapan region."""
    try:
        lat = float(value)
    except (TypeError, ValueError):
        raise ValidationError(_("Latitude must be a number."))
    if not (-90 <= lat <= 90):
        raise ValidationError(_("Latitude must be between -90 and 90."))
    if not (LAT_MIN <= lat <= LAT_MAX):
        raise ValidationError(
            _("Latitude %(lat).5f is outside the Kapan / Syunik region."),
            params={"lat": lat},
        )


def validate_longitude(value: Any) -> None:
    """Check that *value* is a valid WGS-84 longitude within Kapan region."""
    try:
        lng = float(value)
    except (TypeError, ValueError):
        raise ValidationError(_("Longitude must be a number."))
    if not (-180 <= lng <= 180):
        raise ValidationError(_("Longitude must be between -180 and 180."))
    if not (LNG_MIN <= lng <= LNG_MAX):
        raise ValidationError(
            _("Longitude %(lng).5f is outside the Kapan / Syunik region."),
            params={"lng": lng},
        )


# ---------------------------------------------------------------------------
# 4. Image validators
# ---------------------------------------------------------------------------

MAX_IMAGE_SIZE_MB = 5
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def validate_image_size(image) -> None:
    """Reject images larger than MAX_IMAGE_SIZE_MB."""
    max_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
    if image and hasattr(image, "size") and image.size > max_bytes:
        raise ValidationError(
            _("Image file size must not exceed %(max)d MB."),
            params={"max": MAX_IMAGE_SIZE_MB},
        )


def validate_image_type(image) -> None:
    """Reject images whose content-type is not in ALLOWED_IMAGE_TYPES."""
    if image and hasattr(image, "content_type"):
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise ValidationError(
                _("Unsupported image format. Allowed: JPEG, PNG, WebP, GIF.")
            )


# ---------------------------------------------------------------------------
# 5. Status transition validator (callable for DRF serializer validation)
# ---------------------------------------------------------------------------

from .utils import is_valid_status_transition  # noqa: E402


def validate_status_transition(current_status: str, new_status: str) -> None:
    """
    Raise ``ValidationError`` if transitioning from *current_status* to
    *new_status* is not allowed by the business rules.
    """
    if not is_valid_status_transition(current_status, new_status):
        raise ValidationError(
            _("Cannot transition issue status from '%(old)s' to '%(new)s'."),
            params={"old": current_status, "new": new_status},
        )


# ---------------------------------------------------------------------------
# 6. Comment validators
# ---------------------------------------------------------------------------

MIN_COMMENT_LENGTH = 3
MAX_COMMENT_LENGTH = 2000


def validate_comment_body(value: str) -> None:
    """Validate a comment body for minimum/maximum length."""
    stripped = (value or "").strip()
    if len(stripped) < MIN_COMMENT_LENGTH:
        raise ValidationError(
            _("Comment must be at least %(min)d characters long."),
            params={"min": MIN_COMMENT_LENGTH},
        )
    if len(stripped) > MAX_COMMENT_LENGTH:
        raise ValidationError(
            _("Comment must not exceed %(max)d characters."),
            params={"max": MAX_COMMENT_LENGTH},
        )


# ---------------------------------------------------------------------------
# 7. Compound validator factory
# ---------------------------------------------------------------------------

def make_title_validators() -> list:
    """Return the standard list of title validators as a convenience list."""
    return [validate_title_not_empty, validate_title_length, validate_title_no_spam]


def make_coordinate_validators() -> dict[str, list]:
    """Return field-name → validators dict for latitude and longitude."""
    return {
        "latitude":  [validate_latitude],
        "longitude": [validate_longitude],
    }
