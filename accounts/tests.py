"""
Unit tests for the Accounts app.
Covers User model, registration serializer, and authentication views.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


def make_user(username='testuser', role=None, verified=True, national_id='12345678'):
    role = role or User.ROLE_CITIZEN
    return User.objects.create_user(
        username=username,
        password='securepass123',
        email=f'{username}@kapan.am',
        first_name='Արամ',
        last_name='Պետրոսյան',
        role=role,
        verified=verified,
        national_id=national_id,
    )


# ---------------------------------------------------------------------------
# User Model Tests
# ---------------------------------------------------------------------------

class UserModelTest(TestCase):

    def setUp(self):
        self.citizen = make_user('citizen_model', national_id='11111111')
        self.admin = make_user('admin_model', role=User.ROLE_ADMIN, national_id='22222222')

    def test_str_includes_role(self):
        self.assertIn(self.citizen.role, str(self.citizen))

    def test_is_citizen_property_true_for_citizen(self):
        self.assertTrue(self.citizen.is_citizen)

    def test_is_citizen_property_false_for_admin(self):
        self.assertFalse(self.admin.is_citizen)

    def test_is_admin_user_property_true_for_admin(self):
        self.assertTrue(self.admin.is_admin_user)

    def test_is_admin_user_property_false_for_citizen(self):
        self.assertFalse(self.citizen.is_admin_user)

    def test_is_admin_user_true_when_is_staff(self):
        self.citizen.is_staff = True
        self.citizen.save()
        self.assertTrue(self.citizen.is_admin_user)

    def test_default_role_is_citizen(self):
        user = User.objects.create_user(
            username='newuser', password='pass', national_id='33333333'
        )
        self.assertEqual(user.role, User.ROLE_CITIZEN)

    def test_verified_default_false(self):
        user = User.objects.create_user(
            username='newuser2', password='pass', national_id='44444444'
        )
        self.assertFalse(user.verified)

    def test_national_id_is_unique(self):
        from django.db import IntegrityError
        with self.assertRaises(Exception):
            make_user('duplicate', national_id='11111111')

    def test_validate_national_id_accepts_8_digits(self):
        result = User.validate_national_id('12345678')
        self.assertTrue(result)

    def test_validate_national_id_rejects_short(self):
        with self.assertRaises(ValueError):
            User.validate_national_id('123')

    def test_validate_national_id_rejects_letters(self):
        with self.assertRaises(ValueError):
            User.validate_national_id('ABCD1234')

    def test_role_choices_contain_citizen_and_admin(self):
        roles = [c[0] for c in User.ROLE_CHOICES]
        self.assertIn(User.ROLE_CITIZEN, roles)
        self.assertIn(User.ROLE_ADMIN, roles)

    def test_get_full_name_returns_first_last(self):
        full = self.citizen.get_full_name()
        self.assertIn('Արամ', full)
        self.assertIn('Պետրոսյան', full)


# ---------------------------------------------------------------------------
# RegisterSerializer Tests
# ---------------------------------------------------------------------------

class RegisterSerializerTest(TestCase):

    def _valid_data(self, **overrides):
        data = {
            'username': 'newcitizen',
            'email': 'new@kapan.am',
            'first_name': 'Անի',
            'last_name': 'Հովհաննիսյան',
            'password': 'securepass123',
            'password2': 'securepass123',
            'national_id': '87654321',
            'phone': '+37494000000',
            'address': 'Կապան, Սյունիք',
        }
        data.update(overrides)
        return data

    def test_valid_registration(self):
        serializer = RegisterSerializer(data=self._valid_data())
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_password_mismatch_fails(self):
        serializer = RegisterSerializer(data=self._valid_data(password2='different'))
        self.assertFalse(serializer.is_valid())
        self.assertIn('password2', serializer.errors)

    def test_invalid_national_id_fails(self):
        serializer = RegisterSerializer(data=self._valid_data(national_id='123'))
        self.assertFalse(serializer.is_valid())
        self.assertIn('national_id', serializer.errors)

    def test_duplicate_national_id_fails(self):
        make_user('existing', national_id='87654321')
        serializer = RegisterSerializer(data=self._valid_data())
        self.assertFalse(serializer.is_valid())
        self.assertIn('national_id', serializer.errors)

    def test_create_sets_role_to_citizen(self):
        serializer = RegisterSerializer(data=self._valid_data())
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.role, User.ROLE_CITIZEN)

    def test_create_sets_verified_true(self):
        serializer = RegisterSerializer(data=self._valid_data())
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertTrue(user.verified)

    def test_password_is_hashed_after_creation(self):
        serializer = RegisterSerializer(data=self._valid_data())
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertNotEqual(user.password, 'securepass123')
        self.assertTrue(user.check_password('securepass123'))

    def test_password2_not_in_output(self):
        serializer = RegisterSerializer(data=self._valid_data())
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        output = UserSerializer(user)
        self.assertNotIn('password2', output.data)
        self.assertNotIn('password', output.data)


# ---------------------------------------------------------------------------
# UserSerializer Tests
# ---------------------------------------------------------------------------

class UserSerializerTest(TestCase):

    def setUp(self):
        self.citizen = make_user(national_id='55555555')

    def test_serializer_contains_expected_fields(self):
        serializer = UserSerializer(self.citizen)
        data = serializer.data
        for field in ['id', 'username', 'email', 'first_name', 'last_name',
                      'role', 'verified', 'date_joined']:
            self.assertIn(field, data)

    def test_password_not_in_serializer(self):
        serializer = UserSerializer(self.citizen)
        self.assertNotIn('password', serializer.data)

    def test_id_is_read_only(self):
        serializer = UserSerializer(self.citizen, data={'id': 999}, partial=True)
        serializer.is_valid()
        self.assertNotEqual(serializer.validated_data.get('id'), 999)


# ---------------------------------------------------------------------------
# Authentication Web View Tests
# ---------------------------------------------------------------------------

class AuthViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.citizen = make_user(national_id='66666666')

    def test_login_page_loads(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)

    def test_login_with_valid_credentials(self):
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'securepass123',
        }, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_login_with_invalid_credentials(self):
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertNotEqual(response.status_code, 302)

    def test_logout_redirects(self):
        self.client.login(username='testuser', password='securepass123')
        response = self.client.get('/logout/')
        self.assertIn(response.status_code, [200, 302])

    def test_register_page_loads(self):
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# API Auth Tests
# ---------------------------------------------------------------------------

class APIAuthTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.citizen = make_user(national_id='77777777')

    def test_jwt_token_obtain(self):
        response = self.client.post('/api/token/', {
            'username': 'testuser',
            'password': 'securepass123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_jwt_token_refresh(self):
        response = self.client.post('/api/token/', {
            'username': 'testuser',
            'password': 'securepass123',
        })
        refresh_token = response.data['refresh']
        refresh_response = self.client.post('/api/token/refresh/', {
            'refresh': refresh_token
        })
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)

    def test_protected_endpoint_without_token(self):
        response = self.client.get('/api/users/me/')
        self.assertIn(response.status_code, [401, 403])

    def test_protected_endpoint_with_token(self):
        response = self.client.post('/api/token/', {
            'username': 'testuser',
            'password': 'securepass123',
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# accounts/utils.py tests
# ---------------------------------------------------------------------------

class DocumentValidationTest(TestCase):
    def test_valid_national_id(self):
        from accounts.utils import validate_national_id
        self.assertTrue(validate_national_id('123456789'))

    def test_invalid_national_id_too_short(self):
        from accounts.utils import validate_national_id
        self.assertFalse(validate_national_id('12345'))

    def test_invalid_national_id_with_letters(self):
        from accounts.utils import validate_national_id
        self.assertFalse(validate_national_id('AB1234567'))

    def test_valid_passport(self):
        from accounts.utils import validate_passport
        self.assertTrue(validate_passport('AB1234567'))

    def test_invalid_passport_lowercase(self):
        from accounts.utils import validate_passport
        self.assertFalse(validate_passport('ab1234567'))

    def test_validate_document_national_id_ok(self):
        from accounts.utils import validate_document
        ok, err = validate_document('national_id_card', '123456789')
        self.assertTrue(ok)
        self.assertEqual(err, '')

    def test_validate_document_passport_ok(self):
        from accounts.utils import validate_document
        ok, err = validate_document('passport', 'XY9876543')
        self.assertTrue(ok)

    def test_validate_document_wrong_format(self):
        from accounts.utils import validate_document
        ok, err = validate_document('national_id_card', 'WRONG')
        self.assertFalse(ok)
        self.assertIn('9 digits', err)

    def test_validate_document_unknown_type(self):
        from accounts.utils import validate_document
        ok, err = validate_document('alien_id', '123456789')
        self.assertFalse(ok)


class PhoneNormalisationTest(TestCase):
    def test_canonical_format_unchanged(self):
        from accounts.utils import normalise_phone
        self.assertEqual(normalise_phone('+374-77-123456'), '+374-77-123456')

    def test_digits_only_normalised(self):
        from accounts.utils import normalise_phone
        result = normalise_phone('374 77 123456')
        self.assertEqual(result, '+374-77-123456')

    def test_is_valid_phone_true(self):
        from accounts.utils import is_valid_phone
        self.assertTrue(is_valid_phone('+374-77-123456'))

    def test_is_valid_phone_false(self):
        from accounts.utils import is_valid_phone
        self.assertFalse(is_valid_phone('077123456'))


class UserDisplayHelpersTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='displaytest',
            first_name='Gor',
            last_name='Barkhudaryan',
            password='pass1234',
        )

    def test_get_display_name_full_name(self):
        from accounts.utils import get_display_name
        self.assertEqual(get_display_name(self.user), 'Gor Barkhudaryan')

    def test_get_initials_two_letters(self):
        from accounts.utils import get_initials
        self.assertEqual(get_initials(self.user), 'GB')

    def test_get_initials_no_name_uses_username(self):
        from accounts.utils import get_initials
        self.user.first_name = ''
        self.user.last_name = ''
        self.assertEqual(get_initials(self.user), 'DI')  # 'di' from 'displaytest'

    def test_get_role_badge_citizen(self):
        from accounts.utils import get_role_badge
        badge = get_role_badge(self.user)
        self.assertIn('label', badge)

    def test_get_role_badge_admin(self):
        from accounts.utils import get_role_badge
        self.user.role = 'admin'
        badge = get_role_badge(self.user)
        self.assertEqual(badge['label'], 'Admin')


# ---------------------------------------------------------------------------
# accounts/validators.py tests
# ---------------------------------------------------------------------------

class AccountsValidatorsTest(TestCase):
    def test_validate_national_id_format_valid(self):
        from accounts.validators import validate_national_id_format
        validate_national_id_format('123456789')  # should not raise

    def test_validate_national_id_format_passport(self):
        from accounts.validators import validate_national_id_format
        validate_national_id_format('AB1234567')  # passport also valid

    def test_validate_national_id_format_invalid(self):
        from django.core.exceptions import ValidationError
        from accounts.validators import validate_national_id_format
        with self.assertRaises(ValidationError):
            validate_national_id_format('BADVALUE')

    def test_validate_armenian_phone_valid(self):
        from accounts.validators import validate_armenian_phone
        validate_armenian_phone('+374-77-123456')  # should not raise

    def test_validate_armenian_phone_empty_allowed(self):
        from accounts.validators import validate_armenian_phone
        validate_armenian_phone('')  # optional field

    def test_validate_armenian_phone_invalid(self):
        from django.core.exceptions import ValidationError
        from accounts.validators import validate_armenian_phone
        with self.assertRaises(ValidationError):
            validate_armenian_phone('077123456')

    def test_validate_username_format_valid(self):
        from accounts.validators import validate_username_format
        validate_username_format('gor_barkhudaryan')

    def test_validate_username_too_short(self):
        from django.core.exceptions import ValidationError
        from accounts.validators import validate_username_format
        with self.assertRaises(ValidationError):
            validate_username_format('ab')

    def test_validate_username_all_digits(self):
        from django.core.exceptions import ValidationError
        from accounts.validators import validate_username_format
        with self.assertRaises(ValidationError):
            validate_username_format('12345678')

    def test_password_validator_too_short(self):
        from django.core.exceptions import ValidationError
        from accounts.validators import KapantsiPasswordValidator
        v = KapantsiPasswordValidator()
        with self.assertRaises(ValidationError):
            v.validate('abc12')

    def test_password_validator_no_digit(self):
        from django.core.exceptions import ValidationError
        from accounts.validators import KapantsiPasswordValidator
        v = KapantsiPasswordValidator()
        with self.assertRaises(ValidationError):
            v.validate('abcdefgh')

    def test_password_validator_no_letter(self):
        from django.core.exceptions import ValidationError
        from accounts.validators import KapantsiPasswordValidator
        v = KapantsiPasswordValidator()
        with self.assertRaises(ValidationError):
            v.validate('12345678')

    def test_password_validator_valid(self):
        from accounts.validators import KapantsiPasswordValidator
        v = KapantsiPasswordValidator()
        v.validate('securePass1')  # should not raise
