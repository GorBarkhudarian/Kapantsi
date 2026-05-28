"""
dashboard/analytics.py — Platform analytics helpers.

These functions query the database and return structured data suitable for
rendering charts and statistics tables in the admin dashboard.

All functions return plain Python dicts / lists — no HTTP or template logic.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from django.db.models import Count, Q
from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Issue volume over time
# ---------------------------------------------------------------------------

def issues_by_day(days: int = 30) -> list[dict]:
    """
    Return a list of ``{'date': 'YYYY-MM-DD', 'count': N}`` dicts for the
    past *days* calendar days.

    Useful for rendering a line / bar chart of new issues over time.
    """
    from issues.models import Issue

    since = timezone.now().date() - timedelta(days=days)
    qs = (
        Issue.objects.filter(created_at__date__gte=since)
        .extra(select={"day": "date(created_at)"})
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    # Build a dense list (0-fill missing dates)
    by_date: dict[str, int] = {row["day"]: row["count"] for row in qs}
    result = []
    for i in range(days + 1):
        date = (since + timedelta(days=i)).isoformat()
        result.append({"date": date, "count": by_date.get(date, 0)})
    return result


# ---------------------------------------------------------------------------
# 2. Resolution rate
# ---------------------------------------------------------------------------

def resolution_rate() -> dict[str, Any]:
    """
    Return platform-wide resolution statistics.

    Keys:
        total          — total issues
        completed      — resolved issues
        rejected       — rejected issues
        active         — issues still being worked on
        rate_pct       — completed / total × 100 (rounded to 1 dp)
    """
    from issues.models import Issue

    total     = Issue.objects.count()
    completed = Issue.objects.filter(status="completed").count()
    rejected  = Issue.objects.filter(status="rejected").count()
    active    = total - completed - rejected

    rate = round((completed / total * 100), 1) if total else 0.0
    return {
        "total":     total,
        "completed": completed,
        "rejected":  rejected,
        "active":    active,
        "rate_pct":  rate,
    }


# ---------------------------------------------------------------------------
# 3. Top reporters
# ---------------------------------------------------------------------------

def top_reporters(limit: int = 10) -> list[dict]:
    """
    Return the *limit* most active issue reporters.

    Each dict: ``{'username': str, 'full_name': str, 'count': int}``.
    """
    from issues.models import Issue

    rows = (
        Issue.objects.values(
            "created_by__username",
            "created_by__first_name",
            "created_by__last_name",
        )
        .annotate(count=Count("id"))
        .order_by("-count")[:limit]
    )
    return [
        {
            "username":  r["created_by__username"] or "—",
            "full_name": (
                f"{r['created_by__first_name']} {r['created_by__last_name']}".strip()
                or r["created_by__username"]
                or "—"
            ),
            "count": r["count"],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# 4. Issues by category
# ---------------------------------------------------------------------------

def issues_by_category() -> list[dict]:
    """
    Return a list of ``{'category': str, 'label': str, 'count': N}`` dicts,
    ordered by count descending.
    """
    from issues.models import Issue

    rows = (
        Issue.objects.values("category")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    cat_labels = dict(Issue.CATEGORY_CHOICES)
    return [
        {
            "category": r["category"],
            "label":    cat_labels.get(r["category"], r["category"]),
            "count":    r["count"],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# 5. Issues by area
# ---------------------------------------------------------------------------

def issues_by_area() -> list[dict]:
    """
    Return a list of ``{'area': str, 'count': N}`` dicts.
    """
    from issues.models import Issue

    rows = (
        Issue.objects.values("area")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    return [{"area": r["area"] or "unknown", "count": r["count"]} for r in rows]


# ---------------------------------------------------------------------------
# 6. Average time to resolve (in hours)
# ---------------------------------------------------------------------------

def avg_resolution_hours() -> float | None:
    """
    Return the mean number of hours from issue creation to completion,
    or ``None`` if no completed issues exist.

    This is computed in Python to avoid DB-specific date arithmetic.
    """
    from issues.models import Issue

    completed = Issue.objects.filter(
        status="completed", updated_at__isnull=False
    ).values_list("created_at", "updated_at")

    if not completed:
        return None

    total_hours = 0.0
    count = 0
    for created, updated in completed:
        delta = updated - created
        total_hours += delta.total_seconds() / 3600
        count += 1

    return round(total_hours / count, 1) if count else None


# ---------------------------------------------------------------------------
# 7. Voting engagement
# ---------------------------------------------------------------------------

def voting_engagement() -> dict[str, Any]:
    """
    Return voting-related engagement metrics.

    Keys:
        total_votes         — total votes cast
        issues_with_votes   — issues that received at least one vote
        avg_votes_per_issue — mean votes per issue (all issues)
        top_voted           — list of {'issue_id', 'title_en', 'votes'} (top 5)
    """
    from voting.models import Vote
    from issues.models import Issue

    total_votes = Vote.objects.count()
    total_issues = Issue.objects.count()
    issues_with_votes = (
        Issue.objects.annotate(v=Count("votes")).filter(v__gt=0).count()
    )
    avg = round(total_votes / total_issues, 2) if total_issues else 0.0

    top = (
        Issue.objects.annotate(v=Count("votes"))
        .filter(v__gt=0)
        .order_by("-v")[:5]
        .values("id", "title_en", "v")
    )
    top_voted = [
        {"issue_id": r["id"], "title_en": r["title_en"] or "—", "votes": r["v"]}
        for r in top
    ]

    return {
        "total_votes":         total_votes,
        "issues_with_votes":   issues_with_votes,
        "avg_votes_per_issue": avg,
        "top_voted":           top_voted,
    }


# ---------------------------------------------------------------------------
# 8. User growth
# ---------------------------------------------------------------------------

def user_growth(days: int = 30) -> list[dict]:
    """
    Return daily new-user registration counts for the past *days* days.

    Each dict: ``{'date': 'YYYY-MM-DD', 'count': N}``.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    since = timezone.now().date() - timedelta(days=days)
    qs = (
        User.objects.filter(date_joined__date__gte=since)
        .extra(select={"day": "date(date_joined)"})
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    by_date: dict[str, int] = {row["day"]: row["count"] for row in qs}
    result = []
    for i in range(days + 1):
        date = (since + timedelta(days=i)).isoformat()
        result.append({"date": date, "count": by_date.get(date, 0)})
    return result


# ---------------------------------------------------------------------------
# 9. Full summary (used by DashboardStatsAPIView)
# ---------------------------------------------------------------------------

def full_summary() -> dict[str, Any]:
    """
    Return a single dict combining all analytics suitable for the JSON stats
    endpoint at ``/api/dashboard/stats/``.
    """
    try:
        return {
            "resolution":         resolution_rate(),
            "by_category":        issues_by_category(),
            "by_area":            issues_by_area(),
            "top_reporters":      top_reporters(5),
            "voting":             voting_engagement(),
            "avg_resolution_hours": avg_resolution_hours(),
            "issues_last_30_days": issues_by_day(30),
            "user_growth_30_days": user_growth(30),
        }
    except Exception as exc:
        logger.exception("Error building analytics summary: %s", exc)
        return {}
