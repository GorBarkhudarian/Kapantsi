"""
notifications/utils.py — Utility helpers for the Notifications app.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth import get_user_model
    User = get_user_model()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Bulk notification creator
# ---------------------------------------------------------------------------

def create_notification(
    *,
    recipient,
    notif_type: str,
    issue=None,
    message: str = "",
    sender=None,
) -> "Notification | None":
    """
    Create and return a single Notification safely.

    Returns ``None`` and logs a warning if creation fails, so callers never
    need to wrap this in a try/except.
    """
    from .models import Notification  # local import avoids circular deps

    try:
        return Notification.objects.create(
            recipient=recipient,
            notification_type=notif_type,
            issue=issue,
            message=message,
            sender=sender,
        )
    except Exception as exc:
        logger.warning("Failed to create notification for user #%s: %s", recipient.pk, exc)
        return None


def bulk_notify(
    recipients,
    *,
    notif_type: str,
    issue=None,
    message: str = "",
    sender=None,
) -> int:
    """
    Create notifications for multiple *recipients*.

    Returns the number of notifications actually created.
    """
    created = 0
    for user in recipients:
        if create_notification(
            recipient=user,
            notif_type=notif_type,
            issue=issue,
            message=message,
            sender=sender,
        ):
            created += 1
    return created


# ---------------------------------------------------------------------------
# 2. Mark helpers
# ---------------------------------------------------------------------------

def mark_all_read(user) -> int:
    """Mark all unread notifications for *user* as read.

    Returns the number of rows updated.
    """
    from .models import Notification
    return Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)


def get_unread_count(user) -> int:
    """Return the count of unread notifications for *user*."""
    from .models import Notification
    try:
        return Notification.objects.filter(recipient=user, is_read=False).count()
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# 3. Notification type display helpers
# ---------------------------------------------------------------------------

_TYPE_LABELS: dict[str, dict[str, str]] = {
    "status_change": {
        "hy": "Կարգավիճակի փոփոխություն",
        "fr": "Changement de statut",
        "en": "Status Change",
    },
    "new_comment": {
        "hy": "Նոր մեկնաբանություն",
        "fr": "Nouveau commentaire",
        "en": "New Comment",
    },
    "new_vote": {
        "hy": "Նոր ձայն",
        "fr": "Nouveau vote",
        "en": "New Vote",
    },
    "issue_resolved": {
        "hy": "Խնդիրը լուծված է",
        "fr": "Problème résolu",
        "en": "Issue Resolved",
    },
}


def get_type_label(notif_type: str, lang: str = "en") -> str:
    """Return a human-readable label for *notif_type* in *lang*."""
    entry = _TYPE_LABELS.get(notif_type, {})
    return entry.get(lang) or entry.get("en") or notif_type


# ---------------------------------------------------------------------------
# 4. Notification icon colours
# ---------------------------------------------------------------------------

_TYPE_COLORS: dict[str, str] = {
    "status_change": "#4F46E5",
    "new_comment":   "#0EA5E9",
    "new_vote":      "#F59E0B",
    "issue_resolved": "#22C55E",
}


def get_type_color(notif_type: str) -> str:
    """Return a hex colour string for *notif_type* (for icon / badge use)."""
    return _TYPE_COLORS.get(notif_type, "#64748B")
