"""
Management command: send_digest

Send a weekly activity digest email to all verified citizens.

Usage:
    python manage.py send_digest
    python manage.py send_digest --dry-run
    python manage.py send_digest --days 7
    python manage.py send_digest --username specific_user
"""
from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Send a weekly activity digest to all verified citizens"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Include activity from the past N days (default: 7)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print recipient list without sending emails",
        )
        parser.add_argument(
            "--username",
            type=str,
            default=None,
            help="Send digest only to this specific user",
        )

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model
        from issues.models import Issue

        User = get_user_model()
        days = options["days"]
        dry_run = options["dry_run"]
        since = timezone.now() - timedelta(days=days)

        # Collect recipients
        qs = User.objects.filter(is_active=True, verified=True, email__contains="@")
        if options["username"]:
            qs = qs.filter(username=options["username"])

        # Collect recent platform activity
        new_issues = Issue.objects.filter(created_at__gte=since).count()
        resolved   = Issue.objects.filter(
            status="completed", updated_at__gte=since
        ).count()

        sent = 0
        for user in qs:
            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] Would send digest to {user.email} "
                    f"({new_issues} new issues, {resolved} resolved in {days} days)"
                )
                sent += 1
                continue

            try:
                self._send_digest_email(user, new_issues, resolved, days)
                sent += 1
            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f"Failed to send to {user.email}: {exc}")
                )

        label = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{label}Digest sent to {sent} user(s). "
                f"(Last {days} days: {new_issues} new, {resolved} resolved)"
            )
        )

    # ------------------------------------------------------------------

    def _send_digest_email(self, user, new_issues: int, resolved: int, days: int) -> None:
        """
        Compose and send a plain-text digest email to *user*.

        In production this would use Django's send_mail or an email backend.
        For now it uses the console backend configured in settings.
        """
        from django.core.mail import send_mail
        from django.conf import settings

        subject = f"Kapantsi – {days}-day Activity Digest"
        body = (
            f"Hello {user.get_full_name() or user.username},\n\n"
            f"Here is your Kapantsi activity summary for the past {days} days:\n\n"
            f"  • New issues reported:  {new_issues}\n"
            f"  • Issues resolved:      {resolved}\n\n"
            f"Visit the platform to see the latest updates: https://kapantsi.kapan.am\n\n"
            f"— The Kapantsi Team\n"
            f"  Kapan Municipality, Syunik, Armenia\n"
        )
        send_mail(
            subject=subject,
            message=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@kapantsi.kapan.am"),
            recipient_list=[user.email],
            fail_silently=False,
        )
