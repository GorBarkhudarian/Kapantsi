import re
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name',
                  'password', 'password2', 'national_id', 'phone', 'address']

    def validate_national_id(self, value):
        value = str(value).strip()
        if not (re.match(r'^\d{9}$', value) or re.match(r'^[A-Z]{2}\d{7}$', value)):
            raise serializers.ValidationError(
                _('National ID must be 9 digits, or 2 uppercase letters followed by 7 digits for a passport.')
            )
        if User.objects.filter(national_id=value).exists():
            raise serializers.ValidationError(_('This document number is already registered.'))
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': _('Passwords do not match.')})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.role = User.ROLE_CITIZEN
        user.verified = True  # simulate instant verification
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'role', 'verified', 'phone', 'address', 'date_joined']
        read_only_fields = ['id', 'role', 'verified', 'date_joined']
