"""
context_processors.py — Kapantsi global template context

Each processor receives the current request and returns a dict that is merged
into every template's context automatically (configured in settings.py).
"""
from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from issues.models import Issue
from notifications.models import Notification


# ---------------------------------------------------------------------------
# 1. Site-wide metadata
# ---------------------------------------------------------------------------

def site_meta(request) -> dict:
    """
    Expose site-wide constants to every template.

    Available in templates:
        {{ SITE_NAME }}        — "Kapantsi"
        {{ SITE_VERSION }}     — e.g. "1.0.0"
        {{ SITE_CONTACT_EMAIL }}
        {{ DEBUG }}            — True/False (from settings)
    """
    return {
        'SITE_NAME': 'Kapantsi',
        'SITE_VERSION': getattr(settings, 'SITE_VERSION', '1.0.0'),
        'SITE_CONTACT_EMAIL': getattr(settings, 'CONTACT_EMAIL', 'kapantsi@kapan.am'),
        'DEBUG': settings.DEBUG,
    }


# ---------------------------------------------------------------------------
# 2. Platform-level statistics (lightweight — cached-friendly)
# ---------------------------------------------------------------------------

def platform_stats(request) -> dict:
    """
    Provide quick platform statistics to every template.

    Available in templates:
        {{ stats.total }}      — total issue count
        {{ stats.pending }}    — issues awaiting action
        {{ stats.completed }}  — resolved issues
    """
    try:
        qs = Issue.objects.only('status')
        by_status = {s: 0 for s in ('pending', 'under_review', 'in_progress', 'completed', 'rejected')}
        for row in qs.values_list('status', flat=True):
            if row in by_status:
                by_status[row] += 1
        total = sum(by_status.values())
        active = by_status['pending'] + by_status['under_review'] + by_status['in_progress']
        return {
            'stats': {
                'total': total,
                'active': active,
                'pending': by_status['pending'],
                'completed': by_status['completed'],
                'rejected': by_status['rejected'],
            }
        }
    except Exception:
        return {'stats': {'total': 0, 'active': 0, 'pending': 0, 'completed': 0, 'rejected': 0}}


# ---------------------------------------------------------------------------
# 3. Authenticated user extras
# ---------------------------------------------------------------------------

def user_extras(request) -> dict:
    """
    Provide per-user extras (notification badge count) to every template.

    Available in templates:
        {{ unread_notifications }}   — integer badge count for the nav bar
        {{ current_year }}           — current calendar year (for footer)
    """
    unread = 0
    if request.user.is_authenticated:
        try:
            unread = Notification.objects.filter(
                recipient=request.user, is_read=False
            ).count()
        except Exception:
            pass

    return {
        'unread_notifications': unread,
        'current_year': timezone.now().year,
    }


# ---------------------------------------------------------------------------
# 4. Feature flags (simple dict-based feature toggles)
# ---------------------------------------------------------------------------

def feature_flags(request) -> dict:
    """
    Expose feature flags from settings (or defaults) to templates.

    Define in settings.py:
        FEATURE_FLAGS = {
            'MAP_ENABLED':        True,
            'BLOCKCHAIN_ENABLED': False,
            'ANALYTICS_ENABLED':  False,
        }

    Available in templates:
        {% if features.MAP_ENABLED %}…{% endif %}
    """
    defaults = {
        'MAP_ENABLED':        True,
        'BLOCKCHAIN_ENABLED': False,
        'ANALYTICS_ENABLED':  False,
    }
    flags = getattr(settings, 'FEATURE_FLAGS', defaults)
    return {'features': {**defaults, **flags}}
