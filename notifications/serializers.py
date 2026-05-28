"""
Serializers for the Notifications app.
Extended to include issue summary, type label, and user info.
"""
from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Full serializer for Notification model.
    Includes human-readable type label and related issue summary.
    """
    type_display = serializers.SerializerMethodField()
    issue_title = serializers.SerializerMethodField()
    issue_url = serializers.SerializerMethodField()
    time_since = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'type_display',
            'message',
            'message_hy',
            'issue',
            'issue_title',
            'issue_url',
            'read',
            'created_at',
            'time_since',
        ]
        read_only_fields = ['id', 'notification_type', 'message', 'message_hy',
                            'issue', 'created_at']

    def get_type_display(self, obj):
        return obj.get_notification_type_display()

    def get_issue_title(self, obj):
        if obj.issue:
            return obj.issue.title_hy
        return None

    def get_issue_url(self, obj):
        if obj.issue:
            return f'/issues/{obj.issue.pk}/'
        return None

    def get_time_since(self, obj):
        from django.utils import timezone
        from django.utils.timesince import timesince
        if obj.created_at:
            return timesince(obj.created_at, timezone.now())
        return ''


class NotificationMarkReadSerializer(serializers.Serializer):
    """
    Serializer for marking one or many notifications as read.
    Accepts an optional list of notification IDs;
    if omitted, all notifications for the user are marked read.
    """
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text='List of notification IDs to mark as read. Omit to mark all.',
    )


class NotificationSummarySerializer(serializers.Serializer):
    """
    Lightweight serializer for the notification badge/counter in the navbar.
    Returns only the unread count and the most recent unread notification.
    """
    unread_count = serializers.IntegerField(read_only=True)
    latest_message = serializers.CharField(read_only=True, allow_null=True)
    latest_created_at = serializers.DateTimeField(read_only=True, allow_null=True)
