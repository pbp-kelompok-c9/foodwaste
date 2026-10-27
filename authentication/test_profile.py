from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from event_management.models import Event

from .models import Profile

User = get_user_model()
PASSWORD = 'FoodWaste!47-StrongPassword'
JSON = {'HTTP_ACCEPT': 'application/json'}


class ProfileTestBase(TestCase):
    def create_user(self, username='peserta', **profile):
        user = User.objects.create_user(username, f'{username}@example.com', PASSWORD)
        if profile:
            Profile.objects.filter(user=user).update(**profile)
            user.profile.refresh_from_db()
        return user

    def login(self, username='peserta', **profile):
        user = self.create_user(username, **profile)
        self.client.force_login(user)
        return user


class ProfileModelTests(ProfileTestBase):
    def test_profile_created_automatically_for_new_users(self):
        user = self.create_user()
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_name_falls_back_to_username(self):
        user = self.create_user()
        self.assertEqual(user.profile.name, 'peserta')
        user.profile.display_name = 'Peserta Baik'
        self.assertEqual(user.profile.name, 'Peserta Baik')

    def test_to_dict_includes_contact_only_on_request(self):
        user = self.create_user(phone='081234567890', line_id='peserta')
        self.assertNotIn('phone', user.profile.to_dict())
        self.assertEqual(user.profile.to_dict(include_contact=True)['phone'], '081234567890')

    def test_cities_are_distinct_sorted_and_skip_blank(self):
        self.create_user('a', city='Jakarta')
        self.create_user('b', city='Depok')
        self.create_user('c', city='Depok')
        self.create_user('d')
        self.assertEqual(list(Profile.objects.cities()), ['Depok', 'Jakarta'])


class OwnProfileTests(ProfileTestBase):
    def test_pages_require_login(self):
        for name in ['profile', 'profile_json', 'profile_delete']:
            with self.subTest(name=name):
                response = self.client.get(reverse(f'authentication:{name}'))
                self.assertRedirects(response, f"{reverse('authentication:login')}?next={reverse(f'authentication:{name}')}")
        response = self.client.post(reverse('authentication:profile_update'), {'city': 'Depok'})
        self.assertEqual(response.status_code, 302)

    def test_profile_page_shows_own_data_and_contact(self):
        self.login(display_name='Peserta Baik', phone='081234567890')
        response = self.client.get(reverse('authentication:profile'))
        self.assertContains(response, 'Peserta Baik')
        self.assertContains(response, '081234567890')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_missing_profile_is_recreated(self):
        user = self.login()
        Profile.objects.filter(user=user).delete()
        self.assertEqual(self.client.get(reverse('authentication:profile')).status_code, 200)
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_json_includes_contact(self):
        self.login(line_id='peserta')
        data = self.client.get(reverse('authentication:profile_json')).json()['profile']
        self.assertEqual(data['username'], 'peserta')
        self.assertEqual(data['line_id'], 'peserta')


class UpdateProfileTests(ProfileTestBase):
    url = reverse('authentication:profile_update')

    def test_ajax_update_saves_and_returns_json(self):
        user = self.login()
        response = self.client.post(self.url, {
            'display_name': 'Peserta Baik', 'city': '  kota   depok ', 'bio': 'Halo',
            'phone': '+6281234567890', 'line_id': 'peserta',
        }, **JSON)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['profile']['city'], 'Kota Depok')
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.display_name, 'Peserta Baik')
        self.assertEqual(user.profile.phone, '+6281234567890')

    def test_invalid_phone_returns_json_errors(self):
        user = self.login()
        for phone in ['12345', '0812-3456-7890', 'abcdefghij']:
            with self.subTest(phone=phone):
                response = self.client.post(self.url, {'phone': phone}, **JSON)
                self.assertEqual(response.status_code, 400)
                self.assertIn('phone', response.json()['errors'])
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.phone, '')

    def test_html_fallback_redirects_or_rerenders(self):
        self.login()
        response = self.client.post(self.url, {'city': 'Depok'}, follow=True)
        self.assertRedirects(response, reverse('authentication:profile'))
        self.assertContains(response, 'Profil berhasil diperbarui.')
        response = self.client.post(self.url, {'phone': '12'})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.context['form'].errors)

    def test_update_cannot_touch_other_users(self):
        other = self.create_user('lainnya', city='Bogor')
        self.login()
        self.client.post(self.url, {'city': 'Depok', 'user': other.pk, 'username': 'lainnya'}, **JSON)
        other.profile.refresh_from_db()
        self.assertEqual(other.profile.city, 'Bogor')

    def test_update_requires_post(self):
        self.login()
        self.assertEqual(self.client.get(self.url).status_code, 405)


class DeleteAccountTests(ProfileTestBase):
    url = reverse('authentication:profile_delete')

    def test_wrong_confirmation_keeps_account(self):
        user = self.login()
        response = self.client.post(self.url, {'confirm_username': 'salah'}, **JSON)
        self.assertEqual(response.status_code, 400)
        self.assertIn('confirm_username', response.json()['errors'])
        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_ajax_delete_removes_account_and_logs_out(self):
        user = self.login()
        response = self.client.post(self.url, {'confirm_username': 'peserta'}, **JSON)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['redirect'], reverse('authentication:login'))
        self.assertFalse(User.objects.filter(pk=user.pk).exists())
        self.assertFalse(Profile.objects.filter(user_id=user.pk).exists())
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_html_delete_redirects_to_login(self):
        self.login()
        response = self.client.post(self.url, {'confirm_username': 'peserta'})
        self.assertRedirects(response, reverse('authentication:login'))

    def test_account_with_events_cannot_be_deleted(self):
        user = self.login()
        Event.objects.create(name='Festival', event_date=timezone.now(), description='Acara',
                             location='Depok', created_by=user)
        response = self.client.post(self.url, {'confirm_username': 'peserta'}, **JSON)
        self.assertEqual(response.status_code, 400)
        self.assertIn('__all__', response.json()['errors'])
        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_superuser_cannot_delete_from_profile(self):
        admin = User.objects.create_superuser('admin', 'admin@example.com', PASSWORD)
        self.client.force_login(admin)
        response = self.client.post(self.url, {'confirm_username': 'admin'}, **JSON)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(User.objects.filter(pk=admin.pk).exists())

    def test_confirmation_page_renders(self):
        self.login()
        self.assertContains(self.client.get(self.url), 'confirm_username')


class DirectoryTests(ProfileTestBase):
    def setUp(self):
        self.create_user('budi', display_name='Budi Santoso', city='Depok', phone='081111111111')
        self.create_user('sari', display_name='Sari', city='Jakarta', line_id='sari.line')
        self.create_user('rina', display_name='Rina', city='Depok')
        inactive = self.create_user('nonaktif', city='Bandung')
        inactive.is_active = False
        inactive.save()

    def usernames(self, response):
        return [p.user.username for p in response.context['page_obj']]

    def test_contact_hidden_from_anonymous(self):
        response = self.client.get(reverse('authentication:user_list'))
        self.assertNotContains(response, '081111111111')
        self.assertNotContains(response, 'sari.line')
        self.assertContains(response, 'untuk melihat kontak')
        results = self.client.get(reverse('authentication:user_list_json')).json()['results']
        self.assertTrue(all('phone' not in item and 'line_id' not in item for item in results))

    def test_contact_visible_after_login(self):
        self.login()
        self.assertContains(self.client.get(reverse('authentication:user_list')), '081111111111')
        results = self.client.get(reverse('authentication:user_list_json')).json()['results']
        budi = next(item for item in results if item['username'] == 'budi')
        self.assertEqual(budi['phone'], '081111111111')

    def test_filter_by_city_and_query(self):
        url = reverse('authentication:user_list')
        self.assertEqual(self.usernames(self.client.get(url, {'kota': 'Depok'})), ['budi', 'rina'])
        self.assertEqual(self.usernames(self.client.get(url, {'q': 'santoso'})), ['budi'])
        self.assertEqual(self.usernames(self.client.get(url, {'q': 'ri', 'kota': 'depok'})), ['rina'])
        data = self.client.get(reverse('authentication:user_list_json'), {'kota': 'Jakarta'}).json()
        self.assertEqual([item['username'] for item in data['results']], ['sari'])
        self.assertEqual(data['count'], 1)

    def test_inactive_users_hidden(self):
        response = self.client.get(reverse('authentication:user_list'))
        self.assertNotIn('nonaktif', self.usernames(response))
        self.assertNotIn('Bandung', list(response.context['cities']))
        for name in ['user_detail', 'user_detail_json']:
            with self.subTest(name=name):
                url = reverse(f'authentication:{name}', args=['nonaktif'])
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_pagination(self):
        for number in range(10):
            self.create_user(f'warga{number}', city='Bogor')
        url = reverse('authentication:user_list')
        self.assertEqual(len(self.client.get(url).context['page_obj']), 12)
        self.assertEqual(len(self.client.get(url, {'page': 2}).context['page_obj']), 1)
        self.assertEqual(self.client.get(reverse('authentication:user_list_json')).json()['num_pages'], 2)

    def test_user_detail_gates_contact_and_marks_owner(self):
        url = reverse('authentication:user_detail', args=['budi'])
        response = self.client.get(url)
        self.assertContains(response, 'Budi Santoso')
        self.assertNotContains(response, '081111111111')
        self.assertFalse(response.context['is_owner'])
        self.assertNotIn('phone', self.client.get(
            reverse('authentication:user_detail_json', args=['budi'])).json()['profile'])

        self.client.force_login(User.objects.get(username='budi'))
        response = self.client.get(url)
        self.assertContains(response, '081111111111')
        self.assertTrue(response.context['is_owner'])

    def test_unknown_user_returns_404(self):
        self.assertEqual(self.client.get(reverse('authentication:user_detail', args=['tidakada'])).status_code, 404)


class RegisterJsonTests(TestCase):
    url = reverse('authentication:register')

    def test_register_returns_json_and_creates_profile(self):
        response = self.client.post(self.url, dict(
            username='baru', email='baru@example.com', password1=PASSWORD, password2=PASSWORD), **JSON)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['username'], 'baru')
        self.assertTrue(Profile.objects.filter(user__username='baru').exists())

    def test_invalid_register_returns_json_errors(self):
        response = self.client.post(self.url, dict(
            username='baru', email='baru@example.com', password1=PASSWORD, password2='beda'), **JSON)
        self.assertEqual(response.status_code, 400)
        self.assertIn('password2', response.json()['errors'])
        self.assertFalse(User.objects.filter(username='baru').exists())


class ProfileCsrfTests(ProfileTestBase):
    def test_csrf_required_for_profile_actions(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.create_user())
        for name in ['profile_update', 'profile_delete']:
            with self.subTest(name=name):
                self.assertEqual(client.post(reverse(f'authentication:{name}'), {}).status_code, 403)
