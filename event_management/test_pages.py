from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from event_management.models import Event


class EventPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="page_eo")
        cls.owner.groups.add(Group.objects.get_or_create(name="EO")[0])
        cls.participant = get_user_model().objects.create_user(username="page_participant")
        cls.staff = get_user_model().objects.create_user(username="page_staff", is_staff=True)
        cls.superuser = get_user_model().objects.create_superuser(username="page_superuser", password="test-password")
        cls.other_eo = get_user_model().objects.create_user(username="page_other_eo")
        cls.other_eo.groups.add(Group.objects.get(name="EO"))
        cls.event = Event.objects.create(
            name="Acara <script>alert('x')</script>",
            event_date=timezone.now(),
            description="<script>unsafe()</script>\nDeskripsi acara",
            location="Jakarta",
            latitude=Decimal("0.000000"),
            longitude=Decimal("106.827153"),
            created_by=cls.owner,
        )

    @override_settings(LANGUAGE_CODE="id", USE_THOUSAND_SEPARATOR=True)
    def test_public_detail_escapes_content_and_keeps_map_coordinates_url_safe(self):
        response = self.client.get(reverse("event_management:detail", args=[self.event.pk]))
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>alert('x')</script>")
        self.assertNotContains(response, "<script>unsafe()</script>")
        self.assertContains(response, "mlat=0.000000&amp;mlon=106.827153")
        self.assertNotContains(response, "mlon=106,827153")

    def test_eo_without_staff_sees_form_and_manual_location_search(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("event_management:create"))
        self.assertContains(response, 'id="location-search-button"')
        self.assertContains(response, 'type="button" id="location-search-button"')
        self.assertContains(response, "OpenStreetMap contributors")
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertNotContains(response, "/management/")

    def test_manage_actions_are_visible_to_eo_owner_and_superuser(self):
        detail_url = reverse("event_management:detail", args=[self.event.pk])
        edit_url = reverse("event_management:edit", args=[self.event.pk])
        delete_url = reverse("event_management:delete", args=[self.event.pk])
        for user in (self.owner, self.superuser):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.get(detail_url)
                self.assertContains(response, edit_url)
                self.assertContains(response, delete_url)
        for other_user in (self.participant, self.staff, self.other_eo):
            with self.subTest(user=other_user.username):
                self.client.force_login(other_user)
                response = self.client.get(detail_url)
                self.assertNotContains(response, edit_url)
                self.assertNotContains(response, delete_url)

    def test_superuser_without_eo_group_sees_add_event_button(self):
        self.assertFalse(self.superuser.groups.exists())
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("event_management:main"))
        self.assertContains(response, reverse("event_management:create"))

    def test_navigation_shows_events_to_everyone_and_management_to_staff(self):
        url = reverse("event_management:main")
        response = self.client.get(url)
        self.assertContains(response, 'href="/events/"')
        self.assertNotContains(response, 'href="/management/"')
        self.client.force_login(self.staff)
        response = self.client.get(url)
        self.assertContains(response, 'href="/management/"')

    def test_confirmation_get_keeps_event_and_contains_csrf(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("event_management:delete", args=[self.event.pk]))
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, "Ya, hapus acara")
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())
