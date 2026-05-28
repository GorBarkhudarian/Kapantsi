"""
Custom Django template tags and filters for the Kapantsi Issues app.

Usage in templates:
    {% load issue_tags %}

Available tags and filters:
    {% issue_status_badge issue %}          — renders a coloured status badge
    {% issue_category_icon category %}      — returns an SVG icon path for a category
    {{ issue.upvote_count | vote_label }}   — humanises a vote count
    {{ created_at | kapan_date }}           — formats a datetime in Armenian style
    {% localized_status status lang %}      — returns localised status string
    {% localized_category category lang %}  — returns localised category string
    {{ text | truncate_smart:80 }}          — truncates at word boundary
    {% vote_percentage issue total %}       — percentage of votes relative to total
"""
from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

register = template.Library()


# ---------------------------------------------------------------------------
# Status colours and labels
# ---------------------------------------------------------------------------

_STATUS_COLOURS = {
    'pending':      ('bg-yellow-100 text-yellow-800', '⏳'),
    'under_review': ('bg-blue-100 text-blue-800',    '🔍'),
    'in_progress':  ('bg-indigo-100 text-indigo-800','⚙️'),
    'completed':    ('bg-green-100 text-green-800',  '✅'),
    'rejected':     ('bg-red-100 text-red-800',      '❌'),
}

_STATUS_LABELS = {
    'hy': {
        'pending':      'Սպասվում է',
        'under_review': 'Քննության փուլ',
        'in_progress':  'Ընթացքի մեջ',
        'completed':    'Ավարտված',
        'rejected':     'Մերժված',
    },
    'en': {
        'pending':      'Pending',
        'under_review': 'Under Review',
        'in_progress':  'In Progress',
        'completed':    'Completed',
        'rejected':     'Rejected',
    },
    'fr': {
        'pending':      'En attente',
        'under_review': "En cours d'examen",
        'in_progress':  'En cours',
        'completed':    'Terminé',
        'rejected':     'Rejeté',
    },
}

_CATEGORY_LABELS = {
    'hy': {
        'road':        'Ճանապարհ',
        'water':       'Ջուր',
        'electricity': 'Էլեկտրաէներգիա',
        'waste':       'Աղբ',
        'safety':      'Անվտանգություն',
        'other':       'Այլ',
    },
    'en': {
        'road':        'Road',
        'water':       'Water',
        'electricity': 'Electricity',
        'waste':       'Waste',
        'safety':      'Safety',
        'other':       'Other',
    },
    'fr': {
        'road':        'Route',
        'water':       'Eau',
        'electricity': 'Électricité',
        'waste':       'Déchets',
        'safety':      'Sécurité',
        'other':       'Autre',
    },
}

_CATEGORY_COLOURS = {
    'road':        '#F59E0B',
    'water':       '#3B82F6',
    'electricity': '#8B5CF6',
    'waste':       '#10B981',
    'safety':      '#EF4444',
    'other':       '#6B7280',
}


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

@register.simple_tag
def issue_status_badge(issue):
    """
    Render an inline HTML badge for the given issue's status.
    Example: {% issue_status_badge issue %}
    """
    status = getattr(issue, 'status', '') or ''
    css, icon = _STATUS_COLOURS.get(status, ('bg-gray-100 text-gray-700', ''))
    lang = (get_language() or 'en')[:2]
    label = _STATUS_LABELS.get(lang, _STATUS_LABELS['en']).get(status, status)
    html = (
        f'<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full '
        f'text-xs font-semibold {css}">'
        f'{icon} {label}</span>'
    )
    return mark_safe(html)


@register.simple_tag
def issue_category_colour(category):
    """Return the hex colour for a given category slug."""
    return _CATEGORY_COLOURS.get(category, '#6B7280')


@register.simple_tag
def localized_status(status, lang=None):
    """Return the localised label for a status string."""
    lang = (lang or get_language() or 'en')[:2]
    return _STATUS_LABELS.get(lang, _STATUS_LABELS['en']).get(status, status)


@register.simple_tag
def localized_category(category, lang=None):
    """Return the localised label for a category slug."""
    lang = (lang or get_language() or 'en')[:2]
    return _CATEGORY_LABELS.get(lang, _CATEGORY_LABELS['en']).get(category, category)


@register.simple_tag(takes_context=True)
def vote_percentage(context, issue, total):
    """
    Return the percentage of votes this issue has relative to a total.
    Returns 0 if total is zero.
    Example: {% vote_percentage issue total_votes %}
    """
    if not total or total == 0:
        return 0
    try:
        pct = round((issue.upvote_count / total) * 100, 1)
        return pct
    except (ZeroDivisionError, AttributeError, TypeError):
        return 0


@register.inclusion_tag('issues/_status_timeline.html', takes_context=True)
def status_timeline(context, issue):
    """
    Render the status timeline for an issue.
    Requires the partial template issues/_status_timeline.html to exist.
    """
    return {
        'issue': issue,
        'status_history': issue.status_history.all(),
        'request': context.get('request'),
    }


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

@register.filter
def vote_label(count):
    """
    Humanise a vote count.
    0  → '0 votes'
    1  → '1 vote'
    1000 → '1k votes'
    """
    try:
        count = int(count)
    except (TypeError, ValueError):
        return '0 votes'
    if count >= 1000:
        return f'{count / 1000:.1f}k votes'
    if count == 1:
        return '1 vote'
    return f'{count} votes'


@register.filter
def kapan_date(value):
    """
    Format a datetime as a human-readable Armenian-style date string.
    Falls back gracefully if value is None or invalid.
    """
    if not value:
        return ''
    try:
        from django.utils import timezone
        from django.utils.formats import date_format
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return date_format(value, format='j F Y')
    except Exception:
        return str(value)


@register.filter
def truncate_smart(text, length=80):
    """
    Truncate text at a word boundary, appending '...' if truncated.
    Usage: {{ issue.description_hy|truncate_smart:120 }}
    """
    if not text:
        return ''
    text = str(text)
    if len(text) <= length:
        return text
    truncated = text[:length].rsplit(' ', 1)[0]
    return truncated + '...'


@register.filter
def status_colour(status):
    """Return the Tailwind CSS classes for a given status value."""
    css, _ = _STATUS_COLOURS.get(status, ('bg-gray-100 text-gray-700', ''))
    return css


@register.filter
def category_colour_hex(category):
    """Return the hex colour string for a category slug."""
    return _CATEGORY_COLOURS.get(category, '#6B7280')


@register.filter
def unread_count(notifications):
    """Count unread notifications from a queryset."""
    try:
        return notifications.filter(read=False).count()
    except Exception:
        return 0
