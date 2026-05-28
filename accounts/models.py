import re
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    ROLE_CITIZEN = 'citizen'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_CITIZEN, _('Citizen / Քաղաքացի')),
        (ROLE_ADMIN, _('Admin / Ղեկավարման կենտրոն')),
    ]

    DOC_NATIONAL_ID_CARD = 'national_id_card'
    DOC_PASSPORT = 'passport'
    DOC_TYPE_CHOICES = [
        (DOC_NATIONAL_ID_CARD, _('National ID Card')),
        (DOC_PASSPORT, _('Physical Passport')),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_CITIZEN)
    doc_type = models.CharField(
        max_length=20, choices=DOC_TYPE_CHOICES,
        default=DOC_NATIONAL_ID_CARD, blank=True,
        help_text=_('Type of identity document provided'),
    )
    national_id = models.CharField(
        max_length=9, unique=True, null=True, blank=True,
        help_text=_('9-digit national ID card number, or 2 uppercase letters + 7 digits for passport'),
    )
    verified = models.BooleanField(default=False, help_text=_('Citizen identity verified'))
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.role})'

    @property
    def is_citizen(self):
        return self.role == self.ROLE_CITIZEN

    @property
    def is_admin_user(self):
        return self.role == self.ROLE_ADMIN or self.is_staff

    @staticmethod
    def validate_national_id(value):
        if not re.match(r'^\d{9}$', str(value)):
            raise ValueError(_('National ID must be exactly 9 digits'))
        return True


# ---------------------------------------------------------------------------
# About Page Content Model
# ---------------------------------------------------------------------------

class AboutSection(models.Model):
    """
    A single content section displayed on the About page.
    Supports Armenian, French and English content natively.
    Admins can manage all content through the Django admin panel.
    """
    LANG_HY = 'hy'
    LANG_FR = 'fr'
    LANG_EN = 'en'
    LANG_CHOICES = [
        (LANG_HY, _('Armenian')),
        (LANG_FR, _('French')),
        (LANG_EN, _('English')),
    ]

    language = models.CharField(
        max_length=2,
        choices=LANG_CHOICES,
        default=LANG_HY,
        verbose_name=_('Language'),
        db_index=True,
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Display Order'),
        help_text=_('Lower numbers are displayed first.'),
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Section Title'),
    )
    body = models.TextField(
        verbose_name=_('Section Body'),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Inactive sections are hidden from the About page.'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['language', 'order']
        verbose_name = _('About Section')
        verbose_name_plural = _('About Sections')
        indexes = [
            models.Index(fields=['language', 'is_active'], name='about_lang_active_idx'),
        ]

    def __str__(self):
        return f'[{self.get_language_display()}] {self.title}'

    @classmethod
    def get_sections_for_language(cls, lang):
        """Return all active sections for a given language code, ordered by display order."""
        return cls.objects.filter(language=lang, is_active=True).order_by('order')

    @classmethod
    def get_all_languages(cls):
        """Return sections grouped by language as a dict."""
        result = {}
        for lang_code, _ in cls.LANG_CHOICES:
            sections = cls.get_sections_for_language(lang_code)
            result[lang_code] = list(sections.values('title', 'body'))
        return result


# ---------------------------------------------------------------------------
# Email Verification Model
# ---------------------------------------------------------------------------

class EmailVerification(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    code       = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used    = models.BooleanField(default=False)

    def __str__(self):
        return f'Verification for {self.user.username}'
