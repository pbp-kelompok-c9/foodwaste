from unittest.mock import patch
from urllib.parse import urlparse, parse_qs

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from allauth.socialaccount.models import SocialAccount, SocialToken


@override_settings(ROOT_URLCONF='authentication.test_google_urls', GOOGLE_LOGIN_ENABLED=True,
    SOCIALACCOUNT_PROVIDERS={'google': {
        'APPS': [{'client_id': 'test-client', 'secret': 'test-secret', 'key': ''}],
        'SCOPE': ['profile', 'email'], 'OAUTH_PKCE_ENABLED': True,
    }})
class GoogleLoginTests(TestCase):
    def start(self):
        response = self.client.post('/accounts/google/login/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.url).netloc, 'accounts.google.com')
        params = parse_qs(urlparse(response.url).query)
        self.assertIn('code_challenge', params)
        return params['state'][0]

    def complete(self, email='google@example.com', verified=True, state=None):
        if state is None:
            state = self.start()
        with patch('allauth.socialaccount.providers.google.views.GoogleOAuth2Adapter.get_access_token_data',
                   return_value={'access_token': 'fake-token', 'token_type': 'Bearer'}), patch(
                'allauth.socialaccount.providers.google.views.GoogleOAuth2Adapter._fetch_user_info',
                return_value={'id': 'google-123', 'email': email, 'verified_email': verified, 'name': 'Peserta Google'}):
            return self.client.get('/accounts/google/login/callback/', {'code': 'fake-code', 'state': state})

    def test_google_creates_regular_account_and_reuses_it(self):
        response = self.complete()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        user = get_user_model().objects.get(email='google@example.com')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))
        self.assertEqual(SocialAccount.objects.get(user=user).provider, 'google')
        self.assertFalse(SocialToken.objects.exists())
        self.client.logout()
        self.complete()
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))

    def test_existing_local_email_is_not_taken_over(self):
        get_user_model().objects.create_user('local', 'GOOGLE@example.com', 'Other-Password-47!')
        self.assertEqual(self.complete().status_code, 409)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertFalse(SocialAccount.objects.exists())

    def test_unverified_google_email_rejected(self):
        self.assertEqual(self.complete(verified=False).status_code, 403)
        self.assertFalse(get_user_model().objects.exists())

    def test_invalid_state_does_not_exchange_token(self):
        with patch('allauth.socialaccount.providers.google.views.GoogleOAuth2Adapter.get_access_token_data') as exchange:
            self.client.get('/accounts/google/login/callback/', {'code': 'fake-code', 'state': 'invalid-state'})
            exchange.assert_not_called()
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertFalse(get_user_model().objects.exists())

    def test_start_requires_csrf_and_get_does_not_redirect_to_google(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post('/accounts/google/login/').status_code, 403)
        self.assertEqual(client.get('/accounts/google/login/').status_code, 200)

    def test_user_cancels_without_logging_in(self):
        state = self.start()
        response = self.client.get('/accounts/google/login/callback/', {'error': 'access_denied', 'state': state})
        self.assertLess(response.status_code, 500)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_google_button_renders_when_configured(self):
        self.assertContains(self.client.get('/login/'), 'Masuk dengan Google')

    @override_settings(GOOGLE_LOGIN_ENABLED=False)
    def test_google_button_hidden_without_credentials(self):
        self.assertNotContains(self.client.get('/login/'), 'Masuk dengan Google')
