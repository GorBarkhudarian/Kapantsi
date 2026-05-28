"""
voting/utils.py — Utility helpers for the Voting app.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Vote, BlockchainVoteLog

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Vote integrity check
# ---------------------------------------------------------------------------

def compute_vote_hash(vote_id: int, issue_id: int, user_id: int, timestamp: str) -> str:
    """
    Return a SHA-256 hex digest that uniquely identifies a vote record.

    Used to populate ``BlockchainVoteLog.block_hash``.
    """
    data = {
        "vote_id":   vote_id,
        "issue_id":  issue_id,
        "user_id":   user_id,
        "timestamp": timestamp,
    }
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# 2. Vote statistics per issue
# ---------------------------------------------------------------------------

def vote_stats(issue) -> dict:
    """
    Return a dict of voting statistics for *issue*.

    Keys:
        total        — total vote count
        upvotes      — upvotes (currently all votes are upvotes)
        percentage   — upvotes / possible_voters (if available) × 100
    """
    from .models import Vote

    try:
        total = Vote.objects.filter(issue=issue).count()
        return {
            "total":      total,
            "upvotes":    total,
            "percentage": None,  # No denominator without total user count
        }
    except Exception as exc:
        logger.warning("vote_stats error for issue #%s: %s", issue.pk, exc)
        return {"total": 0, "upvotes": 0, "percentage": None}


# ---------------------------------------------------------------------------
# 3. User vote status
# ---------------------------------------------------------------------------

def has_voted(user, issue) -> bool:
    """Return ``True`` if *user* has already voted on *issue*."""
    if not user or not user.is_authenticated:
        return False
    from .models import Vote
    try:
        return Vote.objects.filter(user=user, issue=issue).exists()
    except Exception:
        return False


def toggle_vote(user, issue) -> tuple[bool, str]:
    """
    Toggle *user*'s vote on *issue*.

    Returns ``(voted_now, action)`` where *action* is ``'added'`` or
    ``'removed'``.
    """
    from .models import Vote

    existing = Vote.objects.filter(user=user, issue=issue).first()
    if existing:
        existing.delete()
        return False, "removed"
    Vote.objects.create(user=user, issue=issue)
    return True, "added"


# ---------------------------------------------------------------------------
# 4. Blockchain chain verifier
# ---------------------------------------------------------------------------

def verify_vote_chain(issue=None) -> dict:
    """
    Verify the integrity of the blockchain vote log.

    If *issue* is given, only that issue's chain is checked.
    Returns ``{'valid': bool, 'checked': int, 'errors': list[str]}``.
    """
    from .models import BlockchainVoteLog

    qs = BlockchainVoteLog.objects.order_by("block_id")
    if issue is not None:
        qs = qs.filter(vote__issue=issue)

    errors: list[str] = []
    prev_hash = "0" * 64
    checked = 0

    for log in qs:
        data = {
            "vote_id":   log.vote_id,
            "block_id":  log.block_id,
            "prev_hash": prev_hash,
        }
        expected = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

        if log.block_hash != expected:
            errors.append(
                f"Block {log.block_id}: stored={log.block_hash[:12]}… "
                f"expected={expected[:12]}…"
            )
        prev_hash = log.block_hash
        checked += 1

    return {"valid": len(errors) == 0, "checked": checked, "errors": errors}


# ---------------------------------------------------------------------------
# 5. Top-voted issues
# ---------------------------------------------------------------------------

def top_voted_issues(limit: int = 10):
    """
    Return the *limit* issues with the most votes, ordered descending.

    Returns a queryset annotated with ``vote_count``.
    """
    from django.db.models import Count
    from issues.models import Issue

    return (
        Issue.objects.annotate(vote_count=Count("votes"))
        .filter(vote_count__gt=0)
        .order_by("-vote_count")[:limit]
    )
