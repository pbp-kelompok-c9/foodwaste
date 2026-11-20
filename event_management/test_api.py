from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from food_waste_reporting.models import Report
from .models import Event


class EventAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.owner = users.objects.create_user(username="organizer")
        cls.other = users.objects.create_user(username="other-organizer")
        cls.participant = users.objects.create_user(username="participant")
        cls.admin = users.objects.create_user(username="admin", is_superuser=True)
        group, _ = Group.objects.get_or_create(name="EO")
        cls.owner.groups.add(group)
        cls.other.groups.add(group)
        cls.event = Event.objects.create(
            name="Acara Berbagi", event_date=timezone.now() + timedelta(days=2),
            description="Berbagi makanan", location="Depok", created_by=cls.owner,
        )

    def setUp(self):
        self.list_url = reverse("event_management_api:list")
        self.detail_url = reverse("event_management_api:detail", args=[self.event.pk])
        self.payload = {
            "name": "Acara Baru", "description": "Berbagi makanan",
            "location": "Jakarta", "event_date": (timezone.now() + timedelta(days=3)).isoformat(),
        }

    def login_as(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_public_list_detail_and_search(self):
        result = self.client.get(self.list_url, {"q": "depok"})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["count"], 1)
        self.assertEqual(self.client.get(self.detail_url).status_code, 200)
        self.assertEqual(self.client.get(self.list_url, {"q": "missing"}).data["count"], 0)

    def test_anonymous_and_participant_cannot_create(self):
        self.assertEqual(self.client.post(self.list_url, self.payload, format="json").status_code, 401)
        self.login_as(self.participant)
        self.assertEqual(self.client.post(self.list_url, self.payload, format="json").status_code, 403)

    def test_create_uses_token_user_as_owner(self):
        self.login_as(self.owner)
        result = self.client.post(self.list_url, {**self.payload, "created_by": self.other.pk}, format="json")
        self.assertEqual(result.status_code, 201, result.data)
        self.assertEqual(Event.objects.get(pk=result.data["id"]).created_by, self.owner)

    def test_other_eo_cannot_modify_or_delete(self):
        self.login_as(self.other)
        self.assertEqual(self.client.patch(self.detail_url, {"name": "Changed"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(self.detail_url).status_code, 403)

    def test_owner_can_patch_and_delete(self):
        self.login_as(self.owner)
        result = self.client.patch(self.detail_url, {"name": "Updated"}, format="json")
        self.assertEqual(result.status_code, 200, result.data)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Updated")
        self.assertEqual(self.event.location, "Depok")
        self.assertEqual(self.client.delete(self.detail_url).status_code, 204)

    def test_superuser_can_update_other_owners_event(self):
        self.login_as(self.admin)
        self.assertEqual(self.client.patch(self.detail_url, {"name": "Admin update"}, format="json").status_code, 200)

    def test_invalid_dates_location_and_coordinates_are_rejected(self):
        self.login_as(self.owner)
        for invalid in [
            {"event_date": (timezone.now() - timedelta(days=1)).isoformat()},
            {"location": "   "}, {"latitude": "-6.200000"},
            {"latitude": "91", "longitude": "106"},
        ]:
            with self.subTest(invalid=invalid):
                result = self.client.post(self.list_url, {**self.payload, **invalid}, format="json")
                self.assertEqual(result.status_code, 400, result.data)

    def test_past_event_can_be_edited_without_changing_date(self):
        self.event.event_date = timezone.now() - timedelta(days=3)
        self.event.save()
        self.login_as(self.owner)
        result = self.client.patch(self.detail_url, {"description": "Updated"}, format="json")
        self.assertEqual(result.status_code, 200, result.data)
        original_date = self.event.event_date
        self.event.refresh_from_db()
        self.assertEqual(self.event.event_date, original_date)

    def test_event_with_report_cannot_be_deleted(self):
        Report.objects.create(
            reported_by=self.participant, related_event=self.event,
            food_name="Nasi", food_portion=2, best_before=timezone.now() + timedelta(hours=2),
            location="Stan", event=self.event.name, pickup_option="ambil sendiri", details="",
        )
        self.login_as(self.owner)
        result = self.client.delete(self.detail_url)
        self.assertEqual(result.status_code, 400, result.data)
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())
