"""Serializer Django REST Framework untuk modul User & Authentication.

Validasi registrasi memakai ulang RegistrationForm agar aturan di aplikasi
mobile sama dengan situs web.
"""

from django.contrib.auth import authenticate
from rest_framework import serializers

from .forms import RegistrationForm


def _form_errors(form):
    """Ubah error form Django menjadi dict {field: [pesan, ...]} untuk DRF."""
    return {
        ('non_field_errors' if field == '__all__' else field): [e['message'] for e in errors]
        for field, errors in form.errors.get_json_data().items()
    }


class AccountSerializer(serializers.Serializer):
    """Ringkasan akun yang sedang login, termasuk peran untuk navigasi di aplikasi."""

    def to_representation(self, user):
        return {
            'id': user.pk,
            'username': user.username,
            'email': user.email,
            'is_admin': bool(user.is_staff),
            'is_eo': user.groups.filter(name='EO').exists(),
        }


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password1 = serializers.CharField(write_only=True, trim_whitespace=False)
    password2 = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        # Hanya field eksplisit yang diteruskan; is_staff/role dari klien diabaikan.
        form = RegistrationForm(data=attrs)
        if not form.is_valid():
            raise serializers.ValidationError(_form_errors(form))
        attrs['_form'] = form
        return attrs

    def create(self, validated_data):
        return validated_data['_form'].save()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(self.context.get('request'),
                            username=attrs['username'], password=attrs['password'])
        if user is None:
            raise serializers.ValidationError(
                {'non_field_errors': ['Username atau password salah.']})
        attrs['user'] = user
        return attrs
