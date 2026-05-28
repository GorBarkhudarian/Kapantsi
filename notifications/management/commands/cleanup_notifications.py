"""
Management command: cleanup_notifications

Deletes old read notifications to keep the table lean.

Usage:
    python manage.py cleanup_notifications
    python manage.py cleanup_notifications --days 60
    python manage.py cleanup_notifications --days 30 --dry-run
"""
from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Delete old read notifications older than N days (default 90)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Delete read notifications older than this many days (default: 90)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print how many records would be deleted without actually deleting',
        )
        parser.add_argument(
            '--include-unread',
            action='store_true',
            help='Also delete unread notifications older than --days (use with caution)',
        )

    def handle(self, *args, **options):
        from notifications.models import Notification

        days      = options['days']
        dry_run   = options['dry_run']
        incl_unread = options['include_unread']
        cutoff    = timezone.now() - timedelta(days=days)

        qs = Notification.objects.filter(created_at__lt=cutoff)
        if not incl_unread:
            qs = qs.filter(is_read=True)

        count = qs.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would delete {count} notification(s) older than {days} days"
                    + (" (read only)" if not incl_unread else " (read + unread)")
                )
            )
            return

        deleted, _ = qs.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted} notification(s) older than {days} days."
            )
        )
