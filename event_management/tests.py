from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from food_waste_reporting.models import Report

from .forms import EventForm
from .models import Event
from .permissions import can_manage_event, can_manage_events, is_eo


class EventTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user("event-owner")
        cls.other_eo = User.objects.create_user("event-other-eo")
        cls.participant = User.objects.create_user("event-participant")
        cls.staff = User.objects.create_user("event-staff", is_staff=True)
        cls.superuser = User.objects.create_user("event-superuser", is_staff=True, is_superuser=True)
        group = Group.objects.get_or_create(name="EO")[0]
        cls.owner.groups.add(group)
        cls.other_eo.groups.add(group)
        cls.event = Event.objects.create(
            name="Festival UI", event_date=timezone.now() + timedelta(days=3),
            description="Makanan berlebih dikumpulkan di pintu utama.",
            location="Balairung Depok", created_by=cls.owner,
        )

    def url(self, name, event=None):
        return reverse(f"event_management:{name}", args=[(event or self.event).pk]
                       if name in ("detail", "edit", "delete") else [])

    def data(self, **changes):
        data = {
            "name": "Festival Baru", "event_date": "2027-01-17T09:30",
            "description": "Deskripsi lengkap", "location": "Jakarta",
            "latitude": "-6.200000", "longitude": "106.816666",
        }
        data.update(changes)
        return data


class EventFormTests(EventTestBase):
    def test_form_accepts_wib_time_and_ignores_owner_inputs(self):
        form = EventForm(self.data(created_by=self.other_eo.pk))
        self.assertTrue(form.is_valid(), form.errors)
        local_date = timezone.localtime(form.cleaned_data["event_date"])
        self.assertEqual((local_date.hour, local_date.minute), (9, 30))
        self.assertEqual(local_date.utcoffset(), timedelta(hours=7))
        self.assertNotIn("created_by", form.fields)
        self.assertEqual(form.cleaned_data["latitude"], Decimal("-6.200000"))

    def test_manual_address_without_coordinates_is_valid(self):
        form = EventForm(self.data(latitude="", longitude=""))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["latitude"])
        self.assertIsNone(form.cleaned_data["longitude"])

    def test_invalid_coordinates_and_required_fields_are_rejected(self):
        invalid = [
            {"latitude": "91"}, {"latitude": "-91"},
            {"longitude": "181"}, {"longitude": "-181"},
            {"latitude": ""}, {"longitude": ""},
            {"latitude": "NaN"}, {"latitude": "-6.1234567"},
            {"name": "   "}, {"name": "x" * 201},
            {"description": ""}, {"location": ""}, {"event_date": "invalid"},
        ]
        for values in invalid:
            with self.subTest(values=values):
                self.assertFalse(EventForm(self.data(**values)).is_valid())

    def test_zero_coordinates_and_boundary_values_are_valid(self):
        for lat, lon in (("0", "0"), ("90", "180"), ("-90", "-180")):
            form = EventForm(self.data(latitude=lat, longitude=lon))
            self.assertTrue(form.is_valid(), form.errors)

    def test_edit_form_keeps_local_datetime_value(self):
        form = EventForm(self.data())
        self.assertTrue(form.is_valid(), form.errors)
        event = form.save(commit=False)
        event.created_by = self.owner
        event.save()
        self.assertIn('value="2027-01-17T09:30"', str(EventForm(instance=event)["event_date"]))


class EventModelTests(EventTestBase):
    def test_model_clean_rejects_unpaired_coordinates(self):
        self.event.latitude = Decimal("-6")
        with self.assertRaises(ValidationError):
            self.event.full_clean()

    def test_database_rejects_invalid_or_unpaired_coordinates(self):
        for invalid in (
            {"latitude": Decimal("91"), "longitude": Decimal("1")},
            {"latitude": Decimal("1"), "longitude": Decimal("181")},
            {"latitude": Decimal("1"), "longitude": None},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(IntegrityError):
                with transaction.atomic():
                    Event.objects.filter(pk=self.event.pk).update(**invalid)

    def test_owner_account_is_protected_while_event_exists(self):
        with self.assertRaises(ProtectedError):
            self.owner.delete()


class EventAccessTests(EventTestBase):
    def test_anonymous_can_read_events_but_cannot_manage_them(self):
        for name in ("main", "detail"):
            self.assertEqual(self.client.get(self.url(name)).status_code, 200)
        for name in ("create", "edit", "delete"):
            for method in (self.client.get, self.client.post):
                response = method(self.url(name), self.data())
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("authentication:login"), response.url)
        self.assertEqual(Event.objects.count(), 1)

    def test_staff_and_participant_without_eo_group_are_denied(self):
        for user in (self.participant, self.staff):
            self.client.force_login(user)
            for name in ("create", "edit", "delete"):
                for method in (self.client.get, self.client.post):
                    with self.subTest(user=user.username, action=name, method=method):
                        self.assertEqual(method(self.url(name), self.data()).status_code, 403)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Festival UI")
        self.assertEqual(Event.objects.count(), 1)

    def test_superuser_can_create_events_without_eo_group(self):
        self.assertFalse(self.superuser.groups.exists())
        self.assertFalse(is_eo(self.superuser))
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get(self.url("create")).status_code, 200)
        response = self.client.post(self.url("create"), self.data(created_by=self.owner.pk))
        created = Event.objects.get(name="Festival Baru")
        self.assertRedirects(response, self.url("detail", created))
        self.assertEqual(created.created_by, self.superuser)
        self.assertFalse(self.superuser.groups.exists())

    def test_superuser_can_edit_and_delete_another_owners_event(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get(self.url("edit")).status_code, 200)
        response = self.client.post(
            self.url("edit"), self.data(name="Diperbarui admin", created_by=self.superuser.pk)
        )
        self.assertRedirects(response, self.url("detail"))
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Diperbarui admin")
        self.assertEqual(self.event.created_by, self.owner)
        self.assertEqual(self.client.get(self.url("delete")).status_code, 200)
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())
        self.assertRedirects(self.client.post(self.url("delete")), self.url("main"))
        self.assertFalse(Event.objects.filter(pk=self.event.pk).exists())

    def test_inactive_superuser_does_not_get_event_management_access(self):
        self.superuser.is_active = False
        self.assertFalse(can_manage_events(self.superuser))
        self.assertFalse(can_manage_event(self.superuser, self.event))

    def test_other_eo_cannot_read_edit_confirmation_or_modify_owner_event(self):
        self.client.force_login(self.other_eo)
        for name in ("edit", "delete"):
            for method in (self.client.get, self.client.post):
                self.assertEqual(method(self.url(name), self.data()).status_code, 404)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Festival UI")

    def test_eo_can_create_update_and_delete_own_event_without_staff(self):
        self.assertFalse(self.owner.is_staff)
        self.assertTrue(is_eo(self.owner))
        self.client.force_login(self.owner)
        response = self.client.post(self.url("create"), self.data(created_by=self.other_eo.pk))
        created = Event.objects.get(name="Festival Baru")
        self.assertEqual(created.created_by, self.owner)
        self.assertRedirects(response, self.url("detail", created))
        response = self.client.post(self.url("edit", created), self.data(name="Diubah", created_by=self.other_eo.pk))
        self.assertRedirects(response, self.url("detail", created))
        created.refresh_from_db()
        self.assertEqual(created.name, "Diubah")
        self.assertEqual(created.created_by, self.owner)
        self.assertRedirects(self.client.post(self.url("delete", created)), self.url("main"))
        self.assertFalse(Event.objects.filter(pk=created.pk).exists())

    def test_revoking_eo_membership_revokes_owner_access(self):
        self.client.force_login(self.owner)
        self.owner.groups.clear()
        self.assertFalse(is_eo(self.owner))
        self.assertEqual(self.client.post(self.url("edit"), self.data()).status_code, 403)
        self.assertEqual(self.client.post(self.url("delete")).status_code, 403)

    def test_get_does_not_delete_and_other_http_methods_are_rejected(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.url("delete")).status_code, 200)
        for name in ("create", "edit", "delete"):
            for method in (self.client.put, self.client.patch, self.client.delete):
                self.assertEqual(method(self.url(name)).status_code, 405)
        self.assertEqual(self.client.post(self.url("main")).status_code, 405)
        self.assertEqual(self.client.post(self.url("detail")).status_code, 405)
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())

    def test_csrf_is_required_for_all_mutations(self):
        client = Client(enforce_csrf_checks=True)
        for user in (self.owner, self.superuser):
            client.force_login(user)
            for name in ("create", "edit", "delete"):
                self.assertEqual(client.post(self.url(name), self.data()).status_code, 403)
        client.force_login(self.owner)
        client.get(self.url("create"))
        response = client.post(self.url("create"), self.data(),
                               HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Event.objects.count(), 2)

    def test_invalid_post_shows_errors_and_keeps_original_event(self):
        self.client.force_login(self.owner)
        for name in ("create", "edit"):
            response = self.client.post(self.url(name), self.data(latitude="99"))
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Festival UI")
        self.assertEqual(Event.objects.count(), 1)

    def test_delete_event_with_report_preserves_event_report_and_review(self):
        report = Report.objects.create(
            reported_by=self.participant, food_name="Nasi", food_portion=2,
            best_before=timezone.now(), location="Pintu A", event=self.event.name,
            related_event=self.event, pickup_option="ambil sendiri", details="Utuh",
        )
        for user in (self.owner, self.superuser):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.post(self.url("delete"), follow=True)
                self.assertContains(response, "Acara tidak bisa dihapus karena sudah memiliki laporan.")
                self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())
                self.assertTrue(Report.objects.filter(pk=report.pk).exists())
                self.assertTrue(report.review.is_pending)

    def test_event_search_pagination_and_unknown_ids(self):
        for number in range(13):
            Event.objects.create(name=f"Festival {number}", event_date=timezone.now(),
                                 description="Acara", location="Jakarta", created_by=self.owner)
        response = self.client.get(self.url("main"), {"q": "Jakarta"})
        self.assertEqual(len(response.context["events"]), 12)
        response = self.client.get(self.url("main"), {"q": "Jakarta", "page": 2})
        self.assertEqual(len(response.context["events"]), 1)
        response = self.client.get(self.url("main"), {"q": "Balairung", "page": "invalid"})
        self.assertEqual(list(response.context["events"]), [self.event])
        self.assertEqual(self.client.get(reverse("event_management:detail", args=[99999])).status_code, 404)
        self.client.force_login(self.owner)
        for name in ("edit", "delete"):
            self.assertEqual(self.client.post(reverse(f"event_management:{name}", args=[99999]), self.data()).status_code, 404)


class EoGroupMigrationTests(TransactionTestCase):
    def test_group_is_seeded_and_memberships_survive_rollback_and_reapply(self):
        executor = MigrationExecutor(connection)
        latest_targets = executor.loader.graph.leaf_nodes()
        before = [("event_management", "0001_initial")]
        after = [("event_management", "0002_eo_group")]
        try:
            executor.migrate(before)
            Group.objects.filter(name="EO").delete()
            MigrationExecutor(connection).migrate(after)
            group = Group.objects.get(name="EO")
            user = get_user_model().objects.create_user("migration-eo")
            user.groups.add(group)
            MigrationExecutor(connection).migrate(before)
            self.assertTrue(user.groups.filter(pk=group.pk, name="EO").exists())
            MigrationExecutor(connection).migrate(after)
            self.assertEqual(Group.objects.filter(name="EO").count(), 1)
            self.assertTrue(user.groups.filter(pk=group.pk).exists())
            self.assertFalse(user.is_staff)
        finally:
            MigrationExecutor(connection).migrate(latest_targets)
