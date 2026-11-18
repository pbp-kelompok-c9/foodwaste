from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

User = get_user_model()
PASSWORD = 'FoodWaste!47-StrongPassword'


class AuthAPITests(APITestCase):
    def setUp(self):
        cache.clear()  # reset throttle antar test

    def create_user(self, username='peserta', **kwargs):
        return User.objects.create_user(username, f'{username}@example.com', PASSWORD, **kwargs)

    def test_register_creates_plain_user(self):
        response = self.client.post(reverse('auth_api:register'), {
            'username': 'baru', 'email': 'baru@example.com',
            'password1': PASSWORD, 'password2': PASSWORD,
            'is_staff': True, 'is_superuser': True,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='baru')
        self.assertTrue(user.check_password(PASSWORD))
        self.assertFalse(user.is_staff or user.is_superuser)

    def test_register_rejects_invalid_data(self):
        self.create_user('ada')
        cases = [
            {'password2': 'beda-password-123'},
            {'password1': '123', 'password2': '123'},
            {'email': 'bukan-email'},
            {'username': 'ada'},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                data = {'username': 'baru', 'email': 'baru@example.com',
                        'password1': PASSWORD, 'password2': PASSWORD, **changes}
                response = self.client.post(reverse('auth_api:register'), data, format='json')
                self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username='baru').exists())

    def test_login_returns_token_and_roles(self):
        user = self.create_user()
        user.groups.add(Group.objects.get_or_create(name='EO')[0])
        response = self.client.post(reverse('auth_api:login'),
                                    {'username': 'peserta', 'password': PASSWORD}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['token'], Token.objects.get(user=user).key)
        self.assertTrue(response.data['user']['is_eo'])
        self.assertFalse(response.data['user']['is_admin'])

    def test_login_wrong_password_or_inactive(self):
        self.create_user()
        self.create_user('nonaktif', is_active=False)
        for username, password in [('peserta', 'salah'), ('nonaktif', PASSWORD)]:
            response = self.client.post(reverse('auth_api:login'),
                                        {'username': username, 'password': password}, format='json')
            self.assertEqual(response.status_code, 400)
        self.assertFalse(Token.objects.exists())

    def test_me_and_logout_with_token(self):
        self.assertEqual(self.client.get(reverse('auth_api:me')).status_code, 401)
        token = Token.objects.create(user=self.create_user())
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        self.assertEqual(self.client.get(reverse('auth_api:me')).data['user']['username'], 'peserta')
        self.assertEqual(self.client.post(reverse('auth_api:logout')).status_code, 200)
        self.assertFalse(Token.objects.exists())
        self.assertEqual(self.client.get(reverse('auth_api:me')).status_code, 401)
