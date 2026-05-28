"""
issues/utils.py — Utility helpers for the Issues app.

These are pure-Python functions with no side-effects; they can be imported
and called from views, serializers, management commands, or tests.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import TYPE_CHECKING

from django.utils import timezone

from .models import IssueStatusHistory

if TYPE_CHECKING:
    from .models import Issue

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Status history recorder (existing helper — kept intact)
# ---------------------------------------------------------------------------

def record_status_change(issue, old_status, new_status, user, note=''):
    IssueStatusHistory.objects.create(
        issue=issue,
        old_status=old_status,
        new_status=new_status,
        changed_by=user,
        note=note,
    )
    # Notification is sent by the post_save signal in issues/signals.py


# ---------------------------------------------------------------------------
# 1. Localized title helper
# ---------------------------------------------------------------------------

def get_localized_title(issue: "Issue", lang: str = "en") -> str:
    """Return the best available title for *issue* in the requested *lang*.

    Falls back along the chain:  requested lang → EN → HY → id.
    """
    if lang == "hy":
        return issue.title_hy or issue.title_en or str(issue.pk)
    if lang == "fr":
        return issue.title_fr or issue.title_en or issue.title_hy or str(issue.pk)
    # default: English
    return issue.title_en or issue.title_hy or str(issue.pk)


# ---------------------------------------------------------------------------
# 2. Status transition validator
# ---------------------------------------------------------------------------

_VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending":      {"under_review", "rejected"},
    "under_review": {"in_progress", "rejected"},
    "in_progress":  {"completed", "under_review", "rejected"},
    "completed":    set(),          # terminal — no transitions allowed
    "rejected":     {"pending"},    # allow re-open
}


def is_valid_status_transition(current: str, new: str) -> bool:
    """Return ``True`` if transitioning from *current* to *new* is allowed."""
    return new in _VALID_TRANSITIONS.get(current, set())


def get_allowed_next_statuses(current: str) -> list[str]:
    """Return the list of statuses reachable from *current*."""
    return sorted(_VALID_TRANSITIONS.get(current, set()))


# ---------------------------------------------------------------------------
# 3. Issue scoring (for ranking / "hotness")
# ---------------------------------------------------------------------------

def compute_issue_score(issue: "Issue") -> float:
    """
    Compute a simple time-decayed popularity score.

    score = votes / (age_in_hours + 2) ^ gravity

    Inspired by the Hacker News ranking formula.
    """
    GRAVITY = 1.5
    votes = getattr(issue, "upvote_count", 0) or 0
    age_hours = max(
        (timezone.now() - issue.created_at).total_seconds() / 3600,
        0,
    )
    return votes / ((age_hours + 2) ** GRAVITY)


# ---------------------------------------------------------------------------
# 4. Blockchain / integrity helpers
# ---------------------------------------------------------------------------

def compute_block_hash(data: dict) -> str:
    """
    Return the SHA-256 hex digest of *data* serialised as canonical JSON.

    Used by the BlockchainVoteLog model to build a tamper-evident chain.
    """
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_chain(vote_logs) -> tuple[bool, list[str]]:
    """
    Walk *vote_logs* (ordered queryset of BlockchainVoteLog) and verify that
    each block's stored hash matches a freshly computed hash.

    Returns ``(all_valid, errors)`` where *errors* is a list of human-readable
    problem descriptions.
    """
    errors: list[str] = []
    prev_hash = "0" * 64

    for log in vote_logs:
        data = {
            "vote_id":  log.vote_id,
            "block_id": log.block_id,
            "prev_hash": prev_hash,
        }
        expected = compute_block_hash(data)
        if log.block_hash != expected:
            errors.append(
                f"Block {log.block_id} hash mismatch: "
                f"stored={log.block_hash[:16]}…  expected={expected[:16]}…"
            )
        prev_hash = log.block_hash

    return (len(errors) == 0, errors)


# ---------------------------------------------------------------------------
# 5. Pagination / queryset helpers
# ---------------------------------------------------------------------------

def paginate_queryset(qs, page: int, page_size: int = 20):
    """
    Slice *qs* for page *page* (1-based) with *page_size* items per page.

    Returns ``(items, total_pages, has_next, has_prev)``.
    """
    total = qs.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    items = qs[start: start + page_size]
    return items, total_pages, page < total_pages, page > 1


# ---------------------------------------------------------------------------
# 6. Category colour helpers (mirrors JS tokens — single source of truth)
# ---------------------------------------------------------------------------

CATEGORY_COLORS: dict[str, dict[str, str]] = {
    "road":        {"border": "#4F46E5", "bg": "#EEF2FF", "text": "#4338CA"},
    "water":       {"border": "#1D4ED8", "bg": "#DBEAFE", "text": "#1E40AF"},
    "electricity": {"border": "#D97706", "bg": "#FEF3C7", "text": "#92400E"},
    "waste":       {"border": "#16A34A", "bg": "#DCFCE7", "text": "#14532D"},
    "safety":      {"border": "#DC2626", "bg": "#FEE2E2", "text": "#991B1B"},
    "other":       {"border": "#64748B", "bg": "#F1F5F9", "text": "#334155"},
}


def get_category_colors(category: str) -> dict[str, str]:
    """Return ``{'border': …, 'bg': …, 'text': …}`` for *category*."""
    return CATEGORY_COLORS.get(category, CATEGORY_COLORS["other"])
