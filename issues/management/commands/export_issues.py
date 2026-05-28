"""
Management command: export_issues

Export all issues (or a filtered subset) to CSV or JSON.

Usage:
    python manage.py export_issues
    python manage.py export_issues --format json
    python manage.py export_issues --status completed --format csv
    python manage.py export_issues --category road --output /tmp/road_issues.csv
    python manage.py export_issues --since 2026-01-01
"""
from __future__ import annotations

import csv
import io
import json
import sys
from datetime import datetime, timezone as dt_timezone

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "Export issues to CSV or JSON"

    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            choices=["csv", "json"],
            default="csv",
            help="Output format (default: csv)",
        )
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Output file path (default: stdout)",
        )
        parser.add_argument(
            "--status",
            type=str,
            default=None,
            help="Filter by status (pending, under_review, in_progress, completed, rejected)",
        )
        parser.add_argument(
            "--category",
            type=str,
            default=None,
            help="Filter by category (road, water, electricity, waste, safety, other)",
        )
        parser.add_argument(
            "--since",
            type=str,
            default=None,
            help="Export only issues created on or after this date (YYYY-MM-DD)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of issues to export",
        )

    def handle(self, *args, **options):
        from issues.models import Issue

        qs = Issue.objects.select_related("created_by").order_by("created_at")

        # Apply filters
        if options["status"]:
            qs = qs.filter(status=options["status"])
        if options["category"]:
            qs = qs.filter(category=options["category"])
        if options["since"]:
            try:
                since_dt = datetime.strptime(options["since"], "%Y-%m-%d").replace(
                    tzinfo=dt_timezone.utc
                )
            except ValueError:
                raise CommandError("--since must be in YYYY-MM-DD format")
            qs = qs.filter(created_at__gte=since_dt)
        if options["limit"]:
            qs = qs[: options["limit"]]

        count = qs.count()
        self.stdout.write(self.style.WARNING(f"Exporting {count} issue(s)…"))

        if options["format"] == "csv":
            content = self._to_csv(qs)
        else:
            content = self._to_json(qs)

        if options["output"]:
            with open(options["output"], "w", encoding="utf-8") as fh:
                fh.write(content)
            self.stdout.write(self.style.SUCCESS(f"Written to {options['output']}"))
        else:
            sys.stdout.write(content)

    # ------------------------------------------------------------------

    def _issue_row(self, issue) -> dict:
        return {
            "id":               issue.pk,
            "status":           issue.status,
            "category":         issue.category,
            "area":             issue.area or "",
            "title_hy":         issue.title_hy or "",
            "title_en":         issue.title_en or "",
            "title_fr":         getattr(issue, "title_fr", "") or "",
            "created_by":       issue.created_by.username if issue.created_by else "",
            "created_at":       issue.created_at.isoformat() if issue.created_at else "",
            "updated_at":       issue.updated_at.isoformat() if issue.updated_at else "",
            "latitude":         str(issue.latitude) if issue.latitude else "",
            "longitude":        str(issue.longitude) if issue.longitude else "",
            "location_address": issue.location_address or "",
            "upvote_count":     getattr(issue, "upvote_count", 0) or 0,
        }

    def _to_csv(self, qs) -> str:
        buf = io.StringIO()
        fieldnames = [
            "id", "status", "category", "area",
            "title_hy", "title_en", "title_fr",
            "created_by", "created_at", "updated_at",
            "latitude", "longitude", "location_address", "upvote_count",
        ]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for issue in qs:
            writer.writerow(self._issue_row(issue))
        return buf.getvalue()

    def _to_json(self, qs) -> str:
        rows = [self._issue_row(issue) for issue in qs]
        return json.dumps(rows, ensure_ascii=False, indent=2)
