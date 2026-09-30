from django.contrib.auth import get_user_model
from django.http import HttpResponse
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class GoogleAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return
        verified = any(address.verified and address.email for address in sociallogin.email_addresses)
        if not verified:
            raise ImmediateHttpResponse(HttpResponse(
                'Login Google memerlukan email yang sudah diverifikasi Google.', status=403))
        # Local emails are unverified: never merge accounts just because emails match.
        emails = [address.email for address in sociallogin.email_addresses]
        if any(get_user_model().objects.filter(email__iexact=email).exists() for email in emails):
            raise ImmediateHttpResponse(HttpResponse(
                'Email ini sudah digunakan. Silakan masuk menggunakan username dan password akun yang ada. '
                'Pengaitan akun Google belum tersedia.', status=409))
