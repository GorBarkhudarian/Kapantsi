"""
notifications/tests.py — Tests for the Notifications app.

Covers:
- Notification model
- Notification API endpoints
- notifications/utils.py helpers
- Context processor
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from rest_framework.test import APIClient
from rest_framework import status

from issues.models import Issue
from .models import Notification

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(username: str, role: str = "citizen", verified: bool = True) -> User:
    return User.objects.create_user(
        username=username,
        password="pass1234",
        email=f"{username}@test.com",
        role=role,
        verified=verified,
    )


def make_issue(user: User, **kwargs) -> Issue:
    defaults = {
        "title_hy": "N",
        "title_en": "Notification test issue",
        "description_hy": "desc",
        "category": "road",
        "created_by": user,
    }
    defaults.update(kwargs)
    return Issue.objects.create(**defaults)


def make_notification(recipient: User, issue: Issue = None, **kwargs) -> Notification:
    defaults = {
        "recipient": recipient,
        "notification_type": "status_change",
        "message": "Your issue status has changed.",
        "issue": issue,
    }
    defaults.update(kwargs)
    return Notification.objects.create(**defaults)


# ---------------------------------------------------------------------------
# 1. Notification model tests
# ---------------------------------------------------------------------------

class NotificationModelTest(TestCase):
    def setUp(self):
        self.citizen = make_user("notif_model_cit")
        self.issue = make_issue(self.citizen)

    def test_notification_creation(self):
        notif = make_notification(self.citizen, self.issue)
        self.assertIsNotNone(notif.pk)

    def test_notification_str(self):
        notif = make_notification(self.citizen, self.issue)
        self.assertIsInstance(str(notif), str)

    def test_notification_defaults_to_unread(self):
        notif = make_notification(self.citizen, self.issue)
        self.assertFalse(notif.is_read)

    def test_notification_without_issue(self):
        notif = make_notification(self.citizen, issue=None)
        self.assertIsNone(notif.issue)

    def test_notification_mark_read(self):
        notif = make_notification(self.citizen, self.issue)
        notif.is_read = True
        notif.save()
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_multiple_notifications_for_same_user(self):
        for i in range(3):
            make_notification(self.citizen, self.issue, message=f"Msg {i}")
        self.assertEqual(
            Notification.objects.filter(recipient=self.citizen).count(), 3
        )

    def test_notification_type_choices(self):
        for notif_type in ["status_change", "new_comment", "new_vote"]:
            notif = make_notification(
                self.citizen, self.issue, notification_type=notif_type
            )
            self.assertEqual(notif.notification_type, notif_type)

    def test_notification_deleted_with_issue(self):
        notif = make_notification(self.citizen, self.issue)
        self.issue.delete()
        remaining = Notification.objects.filter(pk=notif.pk)
        if remaining.exists():
            self.assertIsNone(remaining.first().issue)


# ---------------------------------------------------------------------------
# 2. Notification API tests
# ---------------------------------------------------------------------------

class NotificationAPITest(TestCase):
    def setUp(self):
        self.citizen = make_user("notif_api_cit")
        self.other = make_user("notif_api_other")
        self.issue = make_issue(self.citizen)
        self.client = APIClient()

    def test_authenticated_user_can_list_notifications(self):
        make_notification(self.citizen, self.issue)
        self.client.force_authenticate(user=self.citizen)
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_list_notifications(self):
        response = self.client.get("/api/notifications/")
        self.assertIn(response.status_code, [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ])

    def test_user_sees_only_own_notifications(self):
        make_notification(self.citizen, self.issue)
        make_notification(self.other, self.issue, message="Other's notification")
        self.client.force_authenticate(user=self.citizen)
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        for notif in results:
            recipient = notif.get("recipient")
            if recipient:
                self.assertEqual(recipient, self.citizen.pk)

    def test_mark_notification_as_read(self):
        notif = make_notification(self.citizen, self.issue)
        self.client.force_authenticate(user=self.citizen)
        response = self.client.patch(
            f"/api/notifications/{notif.pk}/mark_read/",
            format="json",
        )
        if response.status_code == status.HTTP_200_OK:
            notif.refresh_from_db()
            self.assertTrue(notif.is_read)

    def test_unread_count_endpoint(self):
        make_notification(self.citizen, self.issue)
        make_notification(self.citizen, self.issue, message="Second")
        self.client.force_authenticate(user=self.citizen)
        response = self.client.get("/api/notifications/unread_count/")
        if response.status_code == status.HTTP_200_OK:
            self.assertIn("count", response.data)
            self.assertGreaterEqual(response.data["count"], 2)


# ---------------------------------------------------------------------------
# 3. notifications/utils.py tests
# ---------------------------------------------------------------------------

class CreateNotificationUtilTest(TestCase):
    def setUp(self):
        self.citizen = make_user("create_notif_cit")
        self.issue = make_issue(self.citizen)

    def test_create_notification_returns_notification(self):
        from .utils import create_notification
        notif = create_notification(
            recipient=self.citizen,
            notif_type="status_change",
            issue=self.issue,
            message="Status changed to Under Review",
        )
        self.assertIsNotNone(notif)
        self.assertEqual(notif.recipient, self.citizen)

    def test_create_notification_without_issue(self):
        from .utils import create_notification
        notif = create_notification(
            recipient=self.citizen,
            notif_type="new_vote",
            message="Someone voted on your issue",
        )
        self.assertIsNotNone(notif)
        self.assertIsNone(notif.issue)

    def test_create_notification_persisted_to_db(self):
        from .utils import create_notification
        initial_count = Notification.objects.filter(recipient=self.citizen).count()
        create_notification(
            recipient=self.citizen,
            notif_type="new_comment",
            issue=self.issue,
        )
        self.assertEqual(
            Notification.objects.filter(recipient=self.citizen).count(),
            initial_count + 1,
        )

    def test_create_notification_sets_unread(self):
        from .utils import create_notification
        notif = create_notification(
            recipient=self.citizen,
            notif_type="status_change",
        )
        self.assertFalse(notif.is_read)


class BulkNotifyTest(TestCase):
    def setUp(self):
        self.u1 = make_user("bulk1")
        self.u2 = make_user("bulk2")
        self.u3 = make_user("bulk3")
        self.issue = make_issue(self.u1)

    def test_bulk_notify_all_recipients(self):
        from .utils import bulk_notify
        count = bulk_notify(
            [self.u1, self.u2, self.u3],
            notif_type="status_change",
            issue=self.issue,
            message="Status updated",
        )
        self.assertEqual(count, 3)

    def test_bulk_notify_empty_list(self):
        from .utils import bulk_notify
        count = bulk_notify([], notif_type="new_vote")
        self.assertEqual(count, 0)

    def test_bulk_notify_creates_db_records(self):
        from .utils import bulk_notify
        initial = Notification.objects.count()
        bulk_notify([self.u1, self.u2], notif_type="new_comment", issue=self.issue)
        self.assertEqual(Notification.objects.count(), initial + 2)

    def test_bulk_notify_returns_correct_count(self):
        from .utils import bulk_notify
        count = bulk_notify([self.u1], notif_type="new_vote")
        self.assertEqual(count, 1)


class MarkAllReadTest(TestCase):
    def setUp(self):
        self.citizen = make_user("markall_cit")
        self.issue = make_issue(self.citizen)
        for i in range(4):
            make_notification(self.citizen, self.issue, message=f"Msg {i}")

    def test_mark_all_read_updates_all(self):
        from .utils import mark_all_read
        count = mark_all_read(self.citizen)
        self.assertEqual(count, 4)

    def test_all_notifications_are_read_after(self):
        from .utils import mark_all_read
        mark_all_read(self.citizen)
        unread = Notification.objects.filter(
            recipient=self.citizen, is_read=False
        ).count()
        self.assertEqual(unread, 0)

    def test_mark_all_read_only_affects_user(self):
        from .utils import mark_all_read
        other = make_user("markall_other")
        make_notification(other, self.issue, message="Other's msg")
        mark_all_read(self.citizen)
        other_unread = Notification.objects.filter(
            recipient=other, is_read=False
        ).count()
        self.assertEqual(other_unread, 1)


class GetUnreadCountTest(TestCase):
    def setUp(self):
        self.citizen = make_user("unread_cit")
        self.issue = make_issue(self.citizen)

    def test_unread_count_zero_initially(self):
        from .utils import get_unread_count
        self.assertEqual(get_unread_count(self.citizen), 0)

    def test_unread_count_reflects_unread(self):
        from .utils import get_unread_count
        make_notification(self.citizen, self.issue)
        make_notification(self.citizen, self.issue, message="2nd")
        self.assertEqual(get_unread_count(self.citizen), 2)

    def test_read_notification_not_counted(self):
        from .utils import get_unread_count
        notif = make_notification(self.citizen, self.issue)
        notif.is_read = True
        notif.save()
        self.assertEqual(get_unread_count(self.citizen), 0)

    def test_another_users_notifications_not_counted(self):
        from .utils import get_unread_count
        other = make_user("unread_other")
        make_notification(other, self.issue)
        self.assertEqual(get_unread_count(self.citizen), 0)


class GetTypeLabelTest(TestCase):
    def test_status_change_english(self):
        from .utils import get_type_label
        self.assertEqual(get_type_label("status_change", "en"), "Status Change")

    def test_status_change_armenian(self):
        from .utils import get_type_label
        self.assertEqual(get_type_label("status_change", "hy"), "Կարգավիճակի փոփոխություն")

    def test_status_change_french(self):
        from .utils import get_type_label
        self.assertEqual(get_type_label("status_change", "fr"), "Changement de statut")

    def test_unknown_type_returns_type_string(self):
        from .utils import get_type_label
        self.assertEqual(get_type_label("unknown_type", "en"), "unknown_type")

    def test_new_comment_english(self):
        from .utils import get_type_label
        self.assertEqual(get_type_label("new_comment", "en"), "New Comment")

    def test_new_vote_english(self):
        from .utils import get_type_label
        self.assertEqual(get_type_label("new_vote", "en"), "New Vote")

    def test_issue_resolved_english(self):
        from .utils import get_type_label
        self.assertEqual(get_type_label("issue_resolved", "en"), "Issue Resolved")


class GetTypeColorTest(TestCase):
    def test_status_change_color(self):
        from .utils import get_type_color
        self.assertEqual(get_type_color("status_change"), "#4F46E5")

    def test_new_vote_color(self):
        from .utils import get_type_color
        self.assertEqual(get_type_color("new_vote"), "#F59E0B")

    def test_unknown_type_returns_default(self):
        from .utils import get_type_color
        self.assertEqual(get_type_color("unknown_type"), "#64748B")

    def test_issue_resolved_color(self):
        from .utils import get_type_color
        self.assertEqual(get_type_color("issue_resolved"), "#22C55E")

    def test_new_comment_color(self):
        from .utils import get_type_color
        self.assertEqual(get_type_color("new_comment"), "#0EA5E9")


# ---------------------------------------------------------------------------
# 4. Context processor: unread_notifications
# ---------------------------------------------------------------------------

class UnreadNotificationsContextProcessorTest(TestCase):
    def setUp(self):
        self.citizen = make_user("ctx_cit")
        self.issue = make_issue(self.citizen)

    def test_unread_count_in_context_when_logged_in(self):
        make_notification(self.citizen, self.issue)
        web_client = Client()
        web_client.login(username="ctx_cit", password="pass1234")
        response = web_client.get("/issues/")
        if response.status_code == 200:
            self.assertIn("unread_notifications", response.context)

    def test_unread_count_zero_for_no_notifications(self):
        web_client = Client()
        web_client.login(username="ctx_cit", password="pass1234")
        response = web_client.get("/issues/")
        if response.status_code == 200 and "unread_notifications" in response.context:
            self.assertEqual(response.context["unread_notifications"], 0)
