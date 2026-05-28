"""
Management command: stats_report

Prints a summary of platform statistics to the console.
Useful for quick health checks, demos, and scheduled reports.

Usage:
    python manage.py stats_report
    python manage.py stats_report --format json
"""
import json
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Print a summary of platform statistics.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            choices=['table', 'json'],
            default='table',
            help='Output format: table (default) or json.',
        )

    def handle(self, *args, **options):
        from issues.models import Issue
        from voting.models import Vote, BlockchainVoteLog
        from notifications.models import Notification
        from django.contrib.auth import get_user_model

        User = get_user_model()
        now = timezone.now()

        stats = {
            'generated_at': now.isoformat(),
            'users': {
                'total': User.objects.count(),
                'verified': User.objects.filter(verified=True).count(),
                'citizens': User.objects.filter(role=User.ROLE_CITIZEN).count(),
                'admins': User.objects.filter(role=User.ROLE_ADMIN).count(),
            },
            'issues': {
                'total': Issue.objects.count(),
                'pending': Issue.objects.filter(status='pending').count(),
                'under_review': Issue.objects.filter(status='under_review').count(),
                'in_progress': Issue.objects.filter(status='in_progress').count(),
                'completed': Issue.objects.filter(status='completed').count(),
                'rejected': Issue.objects.filter(status='rejected').count(),
                'by_category': {
                    cat: Issue.objects.filter(category=cat).count()
                    for cat in ['road', 'water', 'electricity', 'waste', 'safety', 'other']
                },
                'city_issues': Issue.objects.filter(area='city').count(),
                'village_issues': Issue.objects.filter(area='village').count(),
            },
            'voting': {
                'total_votes': Vote.objects.count(),
                'blockchain_entries': BlockchainVoteLog.objects.count(),
                'chain_valid': BlockchainVoteLog.verify_chain(),
            },
            'notifications': {
                'total': Notification.objects.count(),
                'unread': Notification.objects.filter(read=False).count(),
            },
        }

        fmt = options['format']

        if fmt == 'json':
            self.stdout.write(json.dumps(stats, indent=2, ensure_ascii=False))
            return

        # Table format
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═' * 52))
        self.stdout.write(self.style.SUCCESS('  KAPANTSI PLATFORM — STATISTICS REPORT'))
        self.stdout.write(self.style.SUCCESS('═' * 52))
        self.stdout.write(f'  Generated: {now.strftime("%Y-%m-%d %H:%M:%S %Z")}')
        self.stdout.write('')

        self.stdout.write(self.style.HTTP_INFO('── USERS ─────────────────────────────────────'))
        u = stats['users']
        self.stdout.write(f'  Total users      : {u["total"]}')
        self.stdout.write(f'  Verified         : {u["verified"]}')
        self.stdout.write(f'  Citizens         : {u["citizens"]}')
        self.stdout.write(f'  Admins           : {u["admins"]}')
        self.stdout.write('')

        self.stdout.write(self.style.HTTP_INFO('── ISSUES ────────────────────────────────────'))
        i = stats['issues']
        self.stdout.write(f'  Total            : {i["total"]}')
        self.stdout.write(f'  Pending          : {i["pending"]}')
        self.stdout.write(f'  Under Review     : {i["under_review"]}')
        self.stdout.write(f'  In Progress      : {i["in_progress"]}')
        self.stdout.write(f'  Completed        : {i["completed"]}')
        self.stdout.write(f'  Rejected         : {i["rejected"]}')
        self.stdout.write(f'  City / Village   : {i["city_issues"]} / {i["village_issues"]}')
        self.stdout.write('')
        self.stdout.write('  By category:')
        for cat, cnt in i['by_category'].items():
            self.stdout.write(f'    {cat:<14}: {cnt}')
        self.stdout.write('')

        self.stdout.write(self.style.HTTP_INFO('── VOTING ────────────────────────────────────'))
        v = stats['voting']
        self.stdout.write(f'  Total votes      : {v["total_votes"]}')
        self.stdout.write(f'  Blockchain blocks: {v["blockchain_entries"]}')
        chain_ok = self.style.SUCCESS('✓ VALID') if v['chain_valid'] else self.style.ERROR('✗ TAMPERED')
        self.stdout.write(f'  Chain integrity  : {chain_ok}')
        self.stdout.write('')

        self.stdout.write(self.style.HTTP_INFO('── NOTIFICATIONS ─────────────────────────────'))
        n = stats['notifications']
        self.stdout.write(f'  Total            : {n["total"]}')
        self.stdout.write(f'  Unread           : {n["unread"]}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═' * 52))
        self.stdout.write('')
