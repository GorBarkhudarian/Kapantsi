from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    TYPE_STATUS_CHANGE = 'status_change'
    TYPE_VOTE = 'vote'
    TYPE_COMMENT = 'comment'
    TYPE_SYSTEM = 'system'
    TYPE_CHOICES = [
        (TYPE_STATUS_CHANGE, _('Status Change')),
        (TYPE_VOTE, _('Vote')),
        (TYPE_COMMENT, _('Comment')),
        (TYPE_SYSTEM, _('System')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_SYSTEM)
    message = models.TextField()
    message_hy = models.TextField(blank=True)
    issue = models.ForeignKey(
        'issues.Issue',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')

    def __str__(self):
        return f'Notification for {self.user}: {self.message[:50]}'
