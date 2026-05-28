"""
Unit tests for the Issues app.
Covers models, serializers, API views, and web views.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .models import Issue, IssueStatusHistory, IssueComment
from .serializers import (
    IssueListSerializer, IssueDetailSerializer,
    IssueCreateSerializer, IssueStatusUpdateSerializer,
    IssueCommentSerializer,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_citizen(username='citizen1', verified=True):
    user = User.objects.create_user(
        username=username,
        password='testpass123',
        email=f'{username}@test.com',
        role=User.ROLE_CITIZEN,
        verified=verified,
        national_id=f'1234567{username[-1] if username[-1].isdigit() else "8"}',
    )
    return user


def make_admin(username='admin1'):
    user = User.objects.create_user(
        username=username,
        password='adminpass123',
        email=f'{username}@test.com',
        role=User.ROLE_ADMIN,
        verified=True,
        is_staff=True,
    )
    return user


def make_issue(created_by=None, **kwargs):
    defaults = dict(
        title_hy='Փողոցի վնասված ծածկ',
        title_en='Damaged road cover',
        description_hy='Ճանապարհի վրա կա վտանգավոր փոս',
        description_en='There is a dangerous pothole on the road',
        category=Issue.CATEGORY_ROAD,
        status=Issue.STATUS_PENDING,
        area=Issue.AREA_CITY,
        latitude=39.2067,
        longitude=46.4058,
    )
    defaults.update(kwargs)
    return Issue.objects.create(created_by=created_by, **defaults)


# ---------------------------------------------------------------------------
# Model Tests
# ---------------------------------------------------------------------------

class IssueModelTest(TestCase):

    def setUp(self):
        self.citizen = make_citizen()
        self.issue = make_issue(created_by=self.citizen)

    def test_str_returns_title_hy(self):
        self.assertEqual(str(self.issue), self.issue.title_hy)

    def test_default_status_is_pending(self):
        self.assertEqual(self.issue.status, Issue.STATUS_PENDING)

    def test_default_upvote_count_is_zero(self):
        self.assertEqual(self.issue.upvote_count, 0)

    def test_get_title_returns_hy_by_default(self):
        self.assertEqual(self.issue.get_title('hy'), self.issue.title_hy)

    def test_get_title_returns_en_when_available(self):
        self.assertEqual(self.issue.get_title('en'), self.issue.title_en)

    def test_get_title_falls_back_to_hy_when_en_empty(self):
        self.issue.title_en = ''
        self.issue.save()
        self.assertEqual(self.issue.get_title('en'), self.issue.title_hy)

    def test_get_description_returns_hy(self):
        self.assertEqual(self.issue.get_description('hy'), self.issue.description_hy)

    def test_get_description_returns_en_when_available(self):
        self.assertEqual(self.issue.get_description('en'), self.issue.description_en)

    def test_get_category_label_road(self):
        label = self.issue.get_category_label()
        self.assertIsInstance(label, str)
        self.assertTrue(len(label) > 0)

    def test_get_status_label_pending(self):
        label = self.issue.get_status_label()
        self.assertIsInstance(label, str)
        self.assertTrue(len(label) > 0)

    def test_get_area_label_city(self):
        label = self.issue.get_area_label()
        self.assertIsInstance(label, str)
        self.assertTrue(len(label) > 0)

    def test_refresh_vote_count_updates_field(self):
        from voting.models import Vote
        citizen2 = make_citizen('citizen2')
        Vote.objects.create(user=citizen2, issue=self.issue)
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.upvote_count, 1)

    def test_ordering_by_upvote_count_then_created_at(self):
        issue2 = make_issue(created_by=self.citizen, title_hy='Երկրորդ խնդիր')
        issue2.upvote_count = 10
        issue2.save()
        issues = list(Issue.objects.all())
        self.assertEqual(issues[0], issue2)

    def test_issue_category_choices_are_valid(self):
        valid = [c[0] for c in Issue.CATEGORY_CHOICES]
        self.assertIn(Issue.CATEGORY_ROAD, valid)
        self.assertIn(Issue.CATEGORY_WATER, valid)
        self.assertIn(Issue.CATEGORY_ELECTRICITY, valid)
        self.assertIn(Issue.CATEGORY_WASTE, valid)
        self.assertIn(Issue.CATEGORY_SAFETY, valid)
        self.assertIn(Issue.CATEGORY_OTHER, valid)

    def test_issue_status_choices_are_valid(self):
        valid = [c[0] for c in Issue.STATUS_CHOICES]
        self.assertIn(Issue.STATUS_PENDING, valid)
        self.assertIn(Issue.STATUS_UNDER_REVIEW, valid)
        self.assertIn(Issue.STATUS_IN_PROGRESS, valid)
        self.assertIn(Issue.STATUS_COMPLETED, valid)
        self.assertIn(Issue.STATUS_REJECTED, valid)

    def test_can_create_issue_without_image(self):
        issue = make_issue(created_by=self.citizen)
        self.assertIsNone(issue.image.name if not issue.image else None)

    def test_area_choices_contain_city_and_village(self):
        valid = [c[0] for c in Issue.AREA_CHOICES]
        self.assertIn(Issue.AREA_CITY, valid)
        self.assertIn(Issue.AREA_VILLAGE, valid)


class IssueStatusHistoryModelTest(TestCase):

    def setUp(self):
        self.citizen = make_citizen()
        self.admin = make_admin()
        self.issue = make_issue(created_by=self.citizen)

    def test_status_history_str(self):
        history = IssueStatusHistory.objects.create(
            issue=self.issue,
            old_status=Issue.STATUS_PENDING,
            new_status=Issue.STATUS_IN_PROGRESS,
            changed_by=self.admin,
        )
        self.assertIn('→', str(history))

    def test_status_history_records_old_and_new(self):
        history = IssueStatusHistory.objects.create(
            issue=self.issue,
            old_status=Issue.STATUS_PENDING,
            new_status=Issue.STATUS_COMPLETED,
            changed_by=self.admin,
            note='Fixed',
        )
        self.assertEqual(history.old_status, Issue.STATUS_PENDING)
        self.assertEqual(history.new_status, Issue.STATUS_COMPLETED)
        self.assertEqual(history.note, 'Fixed')

    def test_multiple_history_entries_ordered_by_time(self):
        IssueStatusHistory.objects.create(
            issue=self.issue, old_status='pending',
            new_status='under_review', changed_by=self.admin,
        )
        IssueStatusHistory.objects.create(
            issue=self.issue, old_status='under_review',
            new_status='in_progress', changed_by=self.admin,
        )
        histories = list(self.issue.status_history.all())
        self.assertEqual(len(histories), 2)
        self.assertEqual(histories[0].new_status, 'under_review')
        self.assertEqual(histories[1].new_status, 'in_progress')


class IssueCommentModelTest(TestCase):

    def setUp(self):
        self.citizen = make_citizen()
        self.issue = make_issue(created_by=self.citizen)

    def test_comment_str(self):
        comment = IssueComment.objects.create(
            issue=self.issue,
            author=self.citizen,
            body='This is a test comment.',
        )
        self.assertIn('Comment by', str(comment))

    def test_comment_belongs_to_issue(self):
        IssueComment.objects.create(
            issue=self.issue, author=self.citizen, body='Comment 1'
        )
        IssueComment.objects.create(
            issue=self.issue, author=self.citizen, body='Comment 2'
        )
        self.assertEqual(self.issue.comments.count(), 2)

    def test_comment_ordering_by_created_at(self):
        c1 = IssueComment.objects.create(
            issue=self.issue, author=self.citizen, body='First'
        )
        c2 = IssueComment.objects.create(
            issue=self.issue, author=self.citizen, body='Second'
        )
        comments = list(self.issue.comments.all())
        self.assertEqual(comments[0], c1)
        self.assertEqual(comments[1], c2)


# ---------------------------------------------------------------------------
# Serializer Tests
# ---------------------------------------------------------------------------

class IssueListSerializerTest(TestCase):

    def setUp(self):
        self.citizen = make_citizen()
        self.issue = make_issue(created_by=self.citizen)

    def test_serializer_contains_expected_fields(self):
        serializer = IssueListSerializer(self.issue)
        data = serializer.data
        self.assertIn('id', data)
        self.assertIn('title_hy', data)
        self.assertIn('category', data)
        self.assertIn('status', data)
        self.assertIn('upvote_count', data)
        self.assertIn('latitude', data)
        self.assertIn('longitude', data)

    def test_created_by_name_returns_username_when_no_fullname(self):
        serializer = IssueListSerializer(self.issue)
        self.assertEqual(serializer.data['created_by_name'], self.citizen.username)

    def test_category_display_is_string(self):
        serializer = IssueListSerializer(self.issue)
        self.assertIsInstance(serializer.data['category_display'], str)

    def test_status_display_is_string(self):
        serializer = IssueListSerializer(self.issue)
        self.assertIsInstance(serializer.data['status_display'], str)

    def test_user_voted_false_without_request(self):
        serializer = IssueListSerializer(self.issue)
        self.assertFalse(serializer.data['user_voted'])


class IssueCreateSerializerTest(TestCase):

    def setUp(self):
        self.citizen = make_citizen()

    def test_valid_data_creates_issue(self):
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = self.citizen
        from rest_framework.request import Request as DRFRequest
        data = {
            'title_hy': 'Նոր խնդիր',
            'description_hy': 'Նկարագրություն',
            'category': Issue.CATEGORY_WATER,
            'area': Issue.AREA_CITY,
            'latitude': 39.2067,
            'longitude': 46.4058,
        }
        serializer = IssueCreateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_required_field_fails(self):
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = self.citizen
        data = {'category': Issue.CATEGORY_ROAD}
        serializer = IssueCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('title_hy', serializer.errors)


class IssueCommentSerializerTest(TestCase):

    def setUp(self):
        self.citizen = make_citizen()
        self.issue = make_issue(created_by=self.citizen)
        self.comment = IssueComment.objects.create(
            issue=self.issue, author=self.citizen, body='Test comment'
        )

    def test_serializer_fields(self):
        serializer = IssueCommentSerializer(self.comment)
        data = serializer.data
        self.assertIn('id', data)
        self.assertIn('body', data)
        self.assertIn('author_name', data)
        self.assertIn('created_at', data)

    def test_author_name_returns_username(self):
        serializer = IssueCommentSerializer(self.comment)
        self.assertEqual(serializer.data['author_name'], self.citizen.username)

    def test_author_name_returns_unknown_when_author_none(self):
        self.comment.author = None
        self.comment.save()
        serializer = IssueCommentSerializer(self.comment)
        self.assertEqual(serializer.data['author_name'], 'Unknown')


# ---------------------------------------------------------------------------
# API View Tests
# ---------------------------------------------------------------------------

class IssueListCreateAPIViewTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.citizen = make_citizen()
        self.issue = make_issue(created_by=self.citizen)

    def test_list_issues_unauthenticated(self):
        response = self.client.get('/api/issues/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_issues_returns_data(self):
        response = self.client.get('/api/issues/')
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_filter_by_category(self):
        make_issue(created_by=self.citizen, category=Issue.CATEGORY_WATER,
                   title_hy='Ջրի խնդիր')
        response = self.client.get('/api/issues/?category=road')
        results = response.data.get('results', [])
        for item in results:
            self.assertEqual(item['category'], 'road')

    def test_filter_by_status(self):
        response = self.client.get('/api/issues/?status=pending')
        results = response.data.get('results', [])
        for item in results:
            self.assertEqual(item['status'], 'pending')

    def test_create_issue_requires_authentication(self):
        data = {
            'title_hy': 'Անանուն խնդիր',
            'description_hy': 'Նկարագրություն',
            'category': Issue.CATEGORY_ROAD,
            'area': Issue.AREA_CITY,
            'latitude': 39.2067,
            'longitude': 46.4058,
        }
        response = self.client.post('/api/issues/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_issue_authenticated(self):
        self.client.force_authenticate(user=self.citizen)
        data = {
            'title_hy': 'Նոր խնդիր',
            'description_hy': 'Նկարագրություն',
            'category': Issue.CATEGORY_ROAD,
            'area': Issue.AREA_CITY,
            'latitude': 39.2067,
            'longitude': 46.4058,
        }
        response = self.client.post('/api/issues/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Issue.objects.count(), 2)

    def test_search_issues_by_title(self):
        response = self.client.get('/api/issues/?search=Փողոց')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class IssueDetailAPIViewTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.citizen = make_citizen()
        self.admin = make_admin()
        self.issue = make_issue(created_by=self.citizen)

    def test_retrieve_issue_unauthenticated(self):
        response = self.client.get(f'/api/issues/{self.issue.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_issue_contains_fields(self):
        response = self.client.get(f'/api/issues/{self.issue.pk}/')
        self.assertIn('id', response.data)
        self.assertIn('title_hy', response.data)
        self.assertIn('description_hy', response.data)
        self.assertIn('comments', response.data)
        self.assertIn('status_history', response.data)

    def test_update_status_requires_admin(self):
        self.client.force_authenticate(user=self.citizen)
        response = self.client.patch(
            f'/api/issues/{self.issue.pk}/',
            {'status': Issue.STATUS_IN_PROGRESS}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_status_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f'/api/issues/{self.issue.pk}/',
            {'status': Issue.STATUS_IN_PROGRESS}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.status, Issue.STATUS_IN_PROGRESS)

    def test_retrieve_nonexistent_issue_returns_404(self):
        response = self.client.get('/api/issues/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class VoteAPIViewTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.citizen = make_citizen()
        self.unverified = make_citizen('unverified', verified=False)
        self.issue = make_issue(created_by=self.citizen)

    def test_vote_requires_authentication(self):
        response = self.client.post(f'/api/issues/{self.issue.pk}/vote/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unverified_citizen_cannot_vote(self):
        self.client.force_authenticate(user=self.unverified)
        response = self.client.post(f'/api/issues/{self.issue.pk}/vote/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_verified_citizen_can_vote(self):
        citizen2 = make_citizen('citizen2')
        self.client.force_authenticate(user=citizen2)
        response = self.client.post(f'/api/issues/{self.issue.pk}/vote/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_vote_twice(self):
        citizen2 = make_citizen('citizen2')
        self.client.force_authenticate(user=citizen2)
        self.client.post(f'/api/issues/{self.issue.pk}/vote/')
        response = self.client.post(f'/api/issues/{self.issue.pk}/vote/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_vote(self):
        citizen2 = make_citizen('citizen2')
        self.client.force_authenticate(user=citizen2)
        self.client.post(f'/api/issues/{self.issue.pk}/vote/')
        response = self.client.delete(f'/api/issues/{self.issue.pk}/vote/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_remove_nonexistent_vote_returns_400(self):
        citizen2 = make_citizen('citizen2')
        self.client.force_authenticate(user=citizen2)
        response = self.client.delete(f'/api/issues/{self.issue.pk}/vote/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vote_increments_upvote_count(self):
        citizen2 = make_citizen('citizen2')
        self.client.force_authenticate(user=citizen2)
        self.client.post(f'/api/issues/{self.issue.pk}/vote/')
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.upvote_count, 1)

    def test_remove_vote_decrements_upvote_count(self):
        citizen2 = make_citizen('citizen2')
        self.client.force_authenticate(user=citizen2)
        self.client.post(f'/api/issues/{self.issue.pk}/vote/')
        self.client.delete(f'/api/issues/{self.issue.pk}/vote/')
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.upvote_count, 0)


# ---------------------------------------------------------------------------
# Web View Tests
# ---------------------------------------------------------------------------

class IssueListWebViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.citizen = make_citizen()
        self.issue = make_issue(created_by=self.citizen)

    def test_issue_list_page_loads(self):
        response = self.client.get('/issues/')
        self.assertEqual(response.status_code, 200)

    def test_issue_list_uses_correct_template(self):
        response = self.client.get('/issues/')
        self.assertTemplateUsed(response, 'issues/list.html')

    def test_issue_list_contains_issues_in_context(self):
        response = self.client.get('/issues/')
        self.assertIn('issues', response.context)

    def test_issue_list_filter_by_category(self):
        response = self.client.get('/issues/?category=road')
        self.assertEqual(response.status_code, 200)

    def test_issue_list_filter_by_status(self):
        response = self.client.get('/issues/?status=pending')
        self.assertEqual(response.status_code, 200)

    def test_issue_list_search(self):
        response = self.client.get('/issues/?search=Փողոց')
        self.assertEqual(response.status_code, 200)


class IssueDetailWebViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.citizen = make_citizen()
        self.issue = make_issue(created_by=self.citizen)

    def test_detail_page_loads(self):
        response = self.client.get(f'/issues/{self.issue.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_detail_page_uses_correct_template(self):
        response = self.client.get(f'/issues/{self.issue.pk}/')
        self.assertTemplateUsed(response, 'issues/detail.html')

    def test_detail_page_contains_issue_in_context(self):
        response = self.client.get(f'/issues/{self.issue.pk}/')
        self.assertEqual(response.context['issue'], self.issue)

    def test_detail_page_nonexistent_returns_404(self):
        response = self.client.get('/issues/99999/')
        self.assertEqual(response.status_code, 404)


class IssueNewWebViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.citizen = make_citizen()

    def test_new_issue_page_requires_login(self):
        response = self.client.get('/issues/new/')
        self.assertNotEqual(response.status_code, 200)

    def test_new_issue_page_loads_when_logged_in(self):
        self.client.login(username='citizen1', password='testpass123')
        response = self.client.get('/issues/new/')
        self.assertEqual(response.status_code, 200)

    def test_new_issue_page_uses_correct_template(self):
        self.client.login(username='citizen1', password='testpass123')
        response = self.client.get('/issues/new/')
        self.assertTemplateUsed(response, 'issues/new.html')


# ---------------------------------------------------------------------------
# utils.py tests
# ---------------------------------------------------------------------------

class GetLocalizedTitleTest(TestCase):
    def setUp(self):
        self.citizen = make_citizen('loctitle')
        self.issue = Issue.objects.create(
            title_hy='Հայ վերնագիր',
            title_en='English title',
            title_fr='Titre français',
            description_hy='Desc',
            category='road',
            created_by=self.citizen,
        )

    def test_english_returns_title_en(self):
        from .utils import get_localized_title
        self.assertEqual(get_localized_title(self.issue, 'en'), 'English title')

    def test_armenian_returns_title_hy(self):
        from .utils import get_localized_title
        self.assertEqual(get_localized_title(self.issue, 'hy'), 'Հայ վերնագիր')

    def test_french_returns_title_fr(self):
        from .utils import get_localized_title
        self.assertEqual(get_localized_title(self.issue, 'fr'), 'Titre français')

    def test_fallback_to_en_when_hy_missing(self):
        from .utils import get_localized_title
        self.issue.title_hy = ''
        self.issue.save()
        self.assertEqual(get_localized_title(self.issue, 'hy'), 'English title')

    def test_fallback_to_pk_when_all_missing(self):
        from .utils import get_localized_title
        self.issue.title_en = ''
        self.issue.title_hy = ''
        self.issue.title_fr = ''
        self.issue.save()
        self.assertEqual(get_localized_title(self.issue, 'en'), str(self.issue.pk))


class StatusTransitionTest(TestCase):
    def test_pending_to_under_review_valid(self):
        from .utils import is_valid_status_transition
        self.assertTrue(is_valid_status_transition('pending', 'under_review'))

    def test_pending_to_completed_invalid(self):
        from .utils import is_valid_status_transition
        self.assertFalse(is_valid_status_transition('pending', 'completed'))

    def test_completed_has_no_transitions(self):
        from .utils import get_allowed_next_statuses
        self.assertEqual(get_allowed_next_statuses('completed'), [])

    def test_rejected_can_reopen_to_pending(self):
        from .utils import is_valid_status_transition
        self.assertTrue(is_valid_status_transition('rejected', 'pending'))

    def test_in_progress_to_completed_valid(self):
        from .utils import is_valid_status_transition
        self.assertTrue(is_valid_status_transition('in_progress', 'completed'))

    def test_unknown_status_returns_false(self):
        from .utils import is_valid_status_transition
        self.assertFalse(is_valid_status_transition('nonexistent', 'pending'))


class CategoryColorsTest(TestCase):
    def test_road_colors(self):
        from .utils import get_category_colors
        colors = get_category_colors('road')
        self.assertIn('border', colors)
        self.assertIn('bg', colors)
        self.assertIn('text', colors)
        self.assertEqual(colors['border'], '#4F46E5')

    def test_unknown_falls_back_to_other(self):
        from .utils import get_category_colors, CATEGORY_COLORS
        colors = get_category_colors('unknown_cat')
        self.assertEqual(colors, CATEGORY_COLORS['other'])


class PaginateQuerysetTest(TestCase):
    def setUp(self):
        self.citizen = make_citizen('paginator')
        for i in range(25):
            Issue.objects.create(
                title_hy=f'Issue {i}',
                title_en=f'Issue {i}',
                description_hy='desc',
                category='road',
                created_by=self.citizen,
            )

    def test_first_page_returns_correct_count(self):
        from .utils import paginate_queryset
        qs = Issue.objects.all()
        items, total_pages, has_next, has_prev = paginate_queryset(qs, 1, 10)
        self.assertEqual(len(items), 10)
        self.assertTrue(has_next)
        self.assertFalse(has_prev)

    def test_last_page_no_next(self):
        from .utils import paginate_queryset
        qs = Issue.objects.all()
        items, total_pages, has_next, has_prev = paginate_queryset(qs, 3, 10)
        self.assertFalse(has_next)
        self.assertTrue(has_prev)

    def test_total_pages_correct(self):
        from .utils import paginate_queryset
        qs = Issue.objects.all()
        _, total_pages, _, _ = paginate_queryset(qs, 1, 10)
        self.assertEqual(total_pages, 3)

    def test_page_clamp_below_1(self):
        from .utils import paginate_queryset
        qs = Issue.objects.all()
        items, total_pages, has_next, has_prev = paginate_queryset(qs, 0, 10)
        # should clamp to page 1
        self.assertFalse(has_prev)


# ---------------------------------------------------------------------------
# validators.py tests
# ---------------------------------------------------------------------------

class TitleValidatorsTest(TestCase):
    def test_empty_title_raises(self):
        from .validators import validate_title_not_empty
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            validate_title_not_empty('')

    def test_whitespace_only_raises(self):
        from .validators import validate_title_not_empty
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            validate_title_not_empty('   ')

    def test_short_title_raises(self):
        from .validators import validate_title_length
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            validate_title_length('Short')

    def test_valid_title_passes(self):
        from .validators import validate_title_length
        validate_title_length('This is a valid issue title for testing')

    def test_all_caps_raises(self):
        from .validators import validate_title_no_spam
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            validate_title_no_spam('ALLCAPSTITLEHERE')

    def test_repeated_chars_raises(self):
        from .validators import validate_title_no_spam
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            validate_title_no_spam('aaaaaaaaaaaaa')


class CoordinateValidatorsTest(TestCase):
    def test_valid_kapan_lat(self):
        from .validators import validate_latitude
        validate_latitude(39.2067)

    def test_out_of_region_lat_raises(self):
        from .validators import validate_latitude
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            validate_latitude(40.5)  # too far north

    def test_valid_kapan_lng(self):
        from .validators import validate_longitude
        validate_longitude(46.4058)

    def test_out_of_region_lng_raises(self):
        from .validators import validate_longitude
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            validate_longitude(45.0)  # west of Kapan

    def test_non_numeric_lat_raises(self):
        from .validators import validate_latitude
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            validate_latitude('not_a_number')


class StatusTransitionValidatorTest(TestCase):
    def test_valid_transition_does_not_raise(self):
        from .validators import validate_status_transition
        validate_status_transition('pending', 'under_review')

    def test_invalid_transition_raises(self):
        from .validators import validate_status_transition
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            validate_status_transition('completed', 'pending')


class CommentValidatorTest(TestCase):
    def test_too_short_raises(self):
        from .validators import validate_comment_body
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            validate_comment_body('Hi')

    def test_valid_comment_passes(self):
        from .validators import validate_comment_body
        validate_comment_body('This is a valid comment for testing purposes.')

    def test_too_long_raises(self):
        from .validators import validate_comment_body
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            validate_comment_body('x' * 2001)


# ---------------------------------------------------------------------------
# permissions.py tests
# ---------------------------------------------------------------------------

class PermissionsTest(TestCase):
    def setUp(self):
        self.citizen = make_citizen('perm_citizen')
        self.unverified = make_citizen('perm_unverified', verified=False)
        self.admin = make_admin('perm_admin')

    def _make_request(self, user):
        from django.test import RequestFactory
        rf = RequestFactory()
        req = rf.get('/')
        req.user = user
        return req

    def test_is_admin_allows_admin(self):
        from .permissions import IsAdminUser
        perm = IsAdminUser()
        req = self._make_request(self.admin)
        self.assertTrue(perm.has_permission(req, None))

    def test_is_admin_rejects_citizen(self):
        from .permissions import IsAdminUser
        perm = IsAdminUser()
        req = self._make_request(self.citizen)
        self.assertFalse(perm.has_permission(req, None))

    def test_is_verified_citizen_allows_verified(self):
        from .permissions import IsVerifiedCitizen
        perm = IsVerifiedCitizen()
        req = self._make_request(self.citizen)
        self.assertTrue(perm.has_permission(req, None))

    def test_is_verified_citizen_rejects_unverified(self):
        from .permissions import IsVerifiedCitizen
        perm = IsVerifiedCitizen()
        req = self._make_request(self.unverified)
        self.assertFalse(perm.has_permission(req, None))

    def test_can_vote_rejects_admin(self):
        from .permissions import CanVote
        perm = CanVote()
        req = self._make_request(self.admin)
        self.assertFalse(perm.has_permission(req, None))
