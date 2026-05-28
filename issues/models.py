from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Issue(models.Model):
    CATEGORY_ROAD = 'road'
    CATEGORY_WATER = 'water'
    CATEGORY_ELECTRICITY = 'electricity'
    CATEGORY_WASTE = 'waste'
    CATEGORY_SAFETY = 'safety'
    CATEGORY_OTHER = 'other'
    CATEGORY_CHOICES = [
        (CATEGORY_ROAD, _('Road / Ճանապարհ')),
        (CATEGORY_WATER, _('Water / Ջուր')),
        (CATEGORY_ELECTRICITY, _('Electricity / Էլեկտրաէներգիա')),
        (CATEGORY_WASTE, _('Waste / Աղբ')),
        (CATEGORY_SAFETY, _('Safety / Անվտանգություն')),
        (CATEGORY_OTHER, _('Other / Այլ')),
    ]

    STATUS_PENDING = 'pending'
    STATUS_UNDER_REVIEW = 'under_review'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending / Սպասվում է')),
        (STATUS_UNDER_REVIEW, _('Under Review / Քննության փուլ')),
        (STATUS_IN_PROGRESS, _('In Progress / Ընթացքի մեջ')),
        (STATUS_COMPLETED, _('Completed / Ավարտված')),
        (STATUS_REJECTED, _('Rejected / Մերժված')),
    ]

    AREA_CITY = 'city'
    AREA_VILLAGE = 'village'
    AREA_CHOICES = [
        (AREA_CITY, _('Kapan City / Կապան քաղաք')),
        (AREA_VILLAGE, _('Village / Գյուղ')),
    ]

    title_hy = models.CharField(max_length=255, verbose_name=_('Title (Armenian)'))
    title_en = models.CharField(max_length=255, blank=True, verbose_name=_('Title (English)'))
    description_hy = models.TextField(verbose_name=_('Description (Armenian)'))
    description_en = models.TextField(blank=True, verbose_name=_('Description (English)'))
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    area = models.CharField(max_length=10, choices=AREA_CHOICES, default=AREA_CITY)
    village_name = models.CharField(max_length=100, blank=True)

    latitude = models.FloatField(default=39.2067)
    longitude = models.FloatField(default=46.4058)
    location_address = models.CharField(max_length=500, blank=True)

    image = models.ImageField(upload_to='issues/', null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_issues'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    upvote_count = models.PositiveIntegerField(default=0)

    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-upvote_count', '-created_at']
        verbose_name = _('Issue')
        verbose_name_plural = _('Issues')

    def __str__(self):
        return self.title_hy

    def get_title(self, lang='hy'):
        if lang == 'en' and self.title_en:
            return self.title_en
        return self.title_hy

    def get_description(self, lang='hy'):
        if lang == 'en' and self.description_en:
            return self.description_en
        return self.description_hy

    def get_category_label(self):
        from django.utils.translation import get_language
        lang = (get_language() or 'en')[:2]
        labels = {
            'hy': {'road': 'Ճանապարհ', 'water': 'Ջուր', 'electricity': 'Էլեկտրաէներգիա',
                   'waste': 'Աղբ', 'safety': 'Անվտանգություն', 'other': 'Այլ'},
            'en': {'road': 'Road', 'water': 'Water', 'electricity': 'Electricity',
                   'waste': 'Waste', 'safety': 'Safety', 'other': 'Other'},
            'fr': {'road': 'Route', 'water': 'Eau', 'electricity': 'Électricité',
                   'waste': 'Déchets', 'safety': 'Sécurité', 'other': 'Autre'},
        }
        return labels.get(lang, labels['en']).get(self.category, self.category)

    def get_status_label(self):
        from django.utils.translation import get_language
        lang = (get_language() or 'en')[:2]
        labels = {
            'hy': {'pending': 'Սպասվում է', 'under_review': 'Քննության փուլ',
                   'in_progress': 'Ընթացքի մեջ', 'completed': 'Ավարտված', 'rejected': 'Մերժված'},
            'en': {'pending': 'Pending', 'under_review': 'Under Review',
                   'in_progress': 'In Progress', 'completed': 'Completed', 'rejected': 'Rejected'},
            'fr': {'pending': 'En attente', 'under_review': 'En cours d\'examen',
                   'in_progress': 'En cours', 'completed': 'Terminé', 'rejected': 'Rejeté'},
        }
        return labels.get(lang, labels['en']).get(self.status, self.status)

    def get_area_label(self):
        from django.utils.translation import get_language
        lang = (get_language() or 'en')[:2]
        labels = {
            'hy': {'city': 'Կապան քաղաք', 'village': 'Գյուղ'},
            'en': {'city': 'Kapan City', 'village': 'Village'},
            'fr': {'city': 'Ville de Kapan', 'village': 'Village'},
        }
        return labels.get(lang, labels['en']).get(self.area, self.area)

    def refresh_vote_count(self):
        self.upvote_count = self.votes.count()
        self.save(update_fields=['upvote_count'])


class IssueStatusHistory(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    note = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['changed_at']
        verbose_name = _('Status History')
        verbose_name_plural = _('Status Histories')

    def __str__(self):
        return f'{self.issue} | {self.old_status} → {self.new_status}'


class IssueComment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author} on {self.issue}'


class IssueImage(models.Model):
    issue      = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='extra_images')
    image      = models.ImageField(upload_to='issues/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f'Image for issue #{self.issue_id}'
