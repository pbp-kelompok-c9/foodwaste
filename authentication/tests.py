from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()
PASSWORD = 'FoodWaste!47-StrongPassword'


class AuthenticationTests(TestCase):
    def registration_data(self, **changes):
        data = dict(username='peserta', email='peserta@example.com',
                    password1=PASSWORD, password2=PASSWORD)
        data.update(changes)
        return data

    def create_user(self, **kwargs):
        return User.objects.create_user('peserta', 'peserta@example.com', PASSWORD, **kwargs)

    def test_register_hashes_password_and_ignores_privilege_fields(self):
        response = self.client.post(reverse('authentication:register'),
                                    self.registration_data(is_staff='true', is_superuser='true', role='admin'))
        self.assertRedirects(response, reverse('authentication:registration_complete'))
        user = User.objects.get(username='peserta')
        self.assertTrue(user.check_password(PASSWORD))
        self.assertNotEqual(user.password, PASSWORD)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_invalid_registration_does_not_create_users(self):
        for changes in [dict(password2='different'), dict(password1='123', password2='123'),
                        dict(email='invalid'), dict(email=''), dict(username='bad name')]:
            with self.subTest(changes=changes):
                response = self.client.post(reverse('authentication:register'), self.registration_data(**changes))
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].errors)
                self.assertFalse(User.objects.exists())

    def test_duplicate_username_rejected(self):
        self.create_user()
        response = self.client.post(reverse('authentication:register'), self.registration_data())
        self.assertIn('username', response.context['form'].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_login_sets_session_and_logout_requires_post(self):
        user = self.create_user()
        response = self.client.post(reverse('authentication:login'), dict(username='peserta', password=PASSWORD))
        self.assertRedirects(response, '/')
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))
        self.assertEqual(self.client.get(reverse('authentication:logout')).status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)
        response = self.client.post(reverse('authentication:logout'))
        self.assertRedirects(response, reverse('authentication:login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_invalid_and_inactive_login_rejected(self):
        user = self.create_user()
        response = self.client.post(reverse('authentication:login'), dict(username='peserta', password='wrong'))
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertNotIn('_auth_user_id', self.client.session)
        user.is_active = False
        user.save()
        response = self.client.post(reverse('authentication:login'), dict(username='peserta', password=PASSWORD))
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_next_redirect_is_local_only(self):
        self.create_user()
        for target, expected in [('/reporting/', '/reporting/'),
                                 ('https://evil.example/', '/'), ('//evil.example/', '/')]:
            with self.subTest(target=target):
                self.client.logout()
                response = self.client.post(reverse('authentication:login'),
                                            dict(username='peserta', password=PASSWORD, next=target))
                self.assertRedirects(response, expected)

    def test_authenticated_users_redirect_from_login_and_register(self):
        self.client.force_login(self.create_user())
        for name in ['login', 'register']:
            self.assertRedirects(self.client.get(reverse('authentication:' + name)), '/')

    def test_csrf_required_for_authentication_actions(self):
        client = Client(enforce_csrf_checks=True)
        for name in ['register', 'login', 'logout']:
            self.assertEqual(client.post(reverse('authentication:' + name), {}).status_code, 403)

    def test_forms_render_with_csrf(self):
        for name in ['register', 'login']:
            self.assertContains(self.client.get(reverse('authentication:' + name)), 'csrfmiddlewaretoken')

    def test_participant_cannot_access_django_admin(self):
        self.client.force_login(self.create_user())
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/admin/login/'))
