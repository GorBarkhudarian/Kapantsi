"""
Django signals for the Issues app.

Signals handled:
    post_save  on Issue         — sends a notification to the reporter when status changes
    post_save  on IssueComment  — notifies the issue reporter of new comments
    post_save  on Vote          — notifies the issue reporter when someone votes
    post_delete on Vote         — updates vote count without creating duplicate notifications
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

logger = logging.getLogger('kapantsi.signals')


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _create_notification(user, notification_type, message, message_hy, issue=None):
    """
    Safely create a Notification, catching any DB errors to avoid
    breaking the main request flow if the notifications table is unavailable.
    """
    try:
        from notifications.models import Notification
        Notification.objects.create(
            user=user,
            notification_type=notification_type,
            message=message,
            message_hy=message_hy,
            issue=issue,
        )
    except Exception as exc:
        logger.warning('Failed to create notification: %s', exc)


# ---------------------------------------------------------------------------
# Issue status-change notification
# ---------------------------------------------------------------------------

@receiver(post_save, sender='issues.Issue')
def notify_on_status_change(sender, instance, created, **kwargs):
    """
    When an issue's status changes, notify the original reporter.
    Skips the initial creation event (no status change yet).
    """
    if created:
        return
    reporter = instance.created_by
    if not reporter:
        return

    # Detect status change via update_fields hint
    update_fields = kwargs.get('update_fields')
    if update_fields is not None and 'status' not in update_fields:
        return

    # Avoid re-notifying on unrelated saves by checking the last history entry
    last_history = instance.status_history.order_by('-changed_at').first()
    if not last_history:
        return

    old = last_history.old_status
    new = last_history.new_status

    if old == new:
        return

    _STATUS_EN = {
        'pending':      'Pending',
        'under_review': 'Under Review',
        'in_progress':  'In Progress',
        'completed':    'Completed',
        'rejected':     'Rejected',
    }
    _STATUS_HY = {
        'pending':      'Սպասվում է',
        'under_review': 'Քննության փուլ',
        'in_progress':  'Ընթացքի մեջ',
        'completed':    'Ավարտված',
        'rejected':     'Մերժված',
    }

    new_label_en = _STATUS_EN.get(new, new)
    new_label_hy = _STATUS_HY.get(new, new)

    _create_notification(
        user=reporter,
        notification_type='status_change',
        message=f'Your issue "{instance.title_hy}" status changed to {new_label_en}.',
        message_hy=f'Ձեր «{instance.title_hy}» հաղորդումի կարգավիճակը փոխվել է՝ {new_label_hy}։',
        issue=instance,
    )
    logger.info(
        'Status change notification sent to %s for issue #%s (%s → %s)',
        reporter.username, instance.pk, old, new,
    )


# ---------------------------------------------------------------------------
# New comment notification
# ---------------------------------------------------------------------------

@receiver(post_save, sender='issues.IssueComment')
def notify_on_new_comment(sender, instance, created, **kwargs):
    """
    When a new comment is posted on an issue, notify the issue reporter —
    unless the commenter IS the reporter.
    """
    if not created:
        return
    issue = instance.issue
    reporter = issue.created_by if issue else None
    commenter = instance.author

    if not reporter:
        return
    if commenter and commenter.pk == reporter.pk:
        return

    commenter_name = commenter.get_full_name() if commenter else 'Someone'
    if not commenter_name:
        commenter_name = commenter.username if commenter else 'Someone'

    _create_notification(
        user=reporter,
        notification_type='comment',
        message=f'{commenter_name} commented on your issue "{issue.title_hy}".',
        message_hy=f'{commenter_name}–ն մեկնաբանություն թողեց ձեր «{issue.title_hy}» հաղորդման վրա։',
        issue=issue,
    )
    logger.info(
        'Comment notification sent to %s for issue #%s',
        reporter.username, issue.pk,
    )


# ---------------------------------------------------------------------------
# Vote notification
# ---------------------------------------------------------------------------

@receiver(post_save, sender='voting.Vote')
def notify_on_vote(sender, instance, created, **kwargs):
    """
    When a new vote is cast, notify the issue reporter —
    unless the voter is the reporter themselves.
    """
    if not created:
        return
    issue = instance.issue
    reporter = issue.created_by if issue else None
    voter = instance.user

    if not reporter:
        return
    if voter and voter.pk == reporter.pk:
        return

    voter_name = voter.get_full_name() if voter else 'Someone'
    if not voter_name:
        voter_name = voter.username if voter else 'Someone'

    _create_notification(
        user=reporter,
        notification_type='vote',
        message=f'{voter_name} voted on your issue "{issue.title_hy}".',
        message_hy=f'{voter_name}–ն քվեարկել է ձեր «{issue.title_hy}» հաղորդման օգտին։',
        issue=issue,
    )
    logger.info(
        'Vote notification sent to %s for issue #%s',
        reporter.username, issue.pk,
    )
