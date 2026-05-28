import re
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

User = get_user_model()

INPUT_CLASS = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent'

_ASCII_ONLY_INPUT   = "this.value=this.value.replace(/[^\\x00-\\x7F]/g,'');"
_ASCII_ONLY_KEYDOWN = ("if(event.key&&event.key.length===1&&event.key.charCodeAt(0)>127)"
                       "{event.preventDefault();}")


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS, 'placeholder': 'Min 6 characters',
            'oninput': _ASCII_ONLY_INPUT, 'onkeydown': _ASCII_ONLY_KEYDOWN,
        }),
        min_length=6, label=_('Password')
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS, 'placeholder': 'Repeat password',
            'oninput': _ASCII_ONLY_INPUT, 'onkeydown': _ASCII_ONLY_KEYDOWN,
        }),
        min_length=6, label=_('Confirm Password')
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'doc_type', 'national_id', 'phone', 'address', 'password', 'password2']
        widgets = {
            'username':    forms.TextInput(attrs={
                'class': INPUT_CLASS, 'placeholder': 'username',
                'oninput': _ASCII_ONLY_INPUT, 'onkeydown': _ASCII_ONLY_KEYDOWN,
            }),
            'first_name':  forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'First name'}),
            'last_name':   forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Last name'}),
            'email':       forms.EmailInput(attrs={
                'class': INPUT_CLASS, 'placeholder': 'email@example.com',
                'oninput': _ASCII_ONLY_INPUT, 'onkeydown': _ASCII_ONLY_KEYDOWN,
            }),
            'doc_type':    forms.HiddenInput(attrs={'id': 'id_doc_type'}),
            'national_id': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': '000000000',
                'id': 'id_national_id',
                'autocomplete': 'off',
                'maxlength': '9',
            }),
            'phone':       forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '+374-077-XXXXXX'}),
            'address':     forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Kapan, Syunik, Armenia'}),
        }

    def clean_national_id(self):
        value = (self.cleaned_data.get('national_id') or '').strip()
        doc_type = self.data.get('doc_type', User.DOC_NATIONAL_ID_CARD)

        if doc_type == User.DOC_PASSPORT:
            if not re.match(r'^[A-Z]{2}\d{7}$', value):
                raise forms.ValidationError(
                    _('Passport number must be 2 uppercase letters followed by 7 digits (e.g. AB1234567).')
                )
        else:
            if not re.match(r'^\d{9}$', value):
                raise forms.ValidationError(
                    _('National ID Card number must be exactly 9 digits.')
                )

        if User.objects.filter(national_id=value).exists():
            raise forms.ValidationError(_('This document number is already registered.'))
        return value

    def clean_phone(self):
        value = self.cleaned_data.get('phone', '').strip()
        if value and not re.match(r'^\+374-\d{2}-\d{6}$', value):
            raise forms.ValidationError(
                _('Phone number must follow the format +374-XX-XXXXXX.')
            )
        return value

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password2'):
            self.add_error('password2', _('Passwords do not match.'))
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = User.ROLE_CITIZEN
        user.verified = True
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput(
            attrs={'class': INPUT_CLASS, 'placeholder': 'Username', 'autofocus': True}
        )
        self.fields['password'].widget = forms.PasswordInput(
            attrs={'class': INPUT_CLASS, 'placeholder': 'Password'}
        )
