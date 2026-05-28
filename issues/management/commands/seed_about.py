"""
Management command: seed_about

Populates the AboutSection database table with the default multilingual
content defined in accounts/about_view.py.

Usage:
    python manage.py seed_about
    python manage.py seed_about --clear   # wipes existing rows first
    python manage.py seed_about --lang hy # seeds only Armenian sections
"""
from django.core.management.base import BaseCommand, CommandError
from accounts.models import AboutSection
from accounts.about_view import SECTIONS_HY, SECTIONS_EN, SECTIONS_FR


CONTENT_MAP = {
    'hy': SECTIONS_HY,
    'en': SECTIONS_EN,
    'fr': SECTIONS_FR,
}


class Command(BaseCommand):
    help = 'Seed the AboutSection table with default multilingual content.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing AboutSection rows before seeding.',
        )
        parser.add_argument(
            '--lang',
            choices=['hy', 'en', 'fr'],
            default=None,
            help='Seed only the specified language (default: all three).',
        )

    def handle(self, *args, **options):
        langs = [options['lang']] if options['lang'] else ['hy', 'en', 'fr']

        if options['clear']:
            deleted, _ = AboutSection.objects.filter(language__in=langs).delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted} existing AboutSection rows.')
            )

        total_created = 0
        for lang in langs:
            sections = CONTENT_MAP[lang]
            for order, section in enumerate(sections, start=1):
                _, created = AboutSection.objects.get_or_create(
                    language=lang,
                    title=section['title'],
                    defaults={
                        'body': section['body'],
                        'order': order,
                        'is_active': True,
                    },
                )
                if created:
                    total_created += 1
                    self.stdout.write(
                        f'  [{lang}] Created: {section["title"][:60]}'
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  [{lang}] Already exists (skipped): {section["title"][:60]}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. Created {total_created} new AboutSection row(s).'
            )
        )
