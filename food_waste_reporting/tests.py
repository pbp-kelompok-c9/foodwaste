from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from discovery_dashboard.models import DiscoveryReport
from event_management.models import Event
from food_waste_reporting.forms import ReportForm
from food_waste_reporting.models import Report

import shutil
import tempfile
import uuid
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

TEMP_MEDIA = tempfile.mkdtemp()


def make_image(name="foto.png"):
    buf = BytesIO()
    Image.new("RGB", (10, 10)).save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")

def make_big_image(name="besar.png", size_mb=6):
    buf = BytesIO()
    Image.new("RGB", (10, 10)).save(buf, "PNG")
    buf.write(b"\0" * (size_mb * 1024 * 1024))     # padding sampai > 5 MB
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ReportBase(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user("owner")
        cls.other = User.objects.create_user("other")
        cls.eo = User.objects.create_user("eo-extra")
        cls.event = Event.objects.create(
            name="Bazar Kampus",
            event_date=timezone.now() + timedelta(days=2),
            location="Balairung", description="x", created_by=cls.eo,
        )

    def form_data(self, **extra):
        data = {
            "food_name": "Nasi Kotak", "food_portion": 5,
            "best_before": (timezone.localdate() + timedelta(days=3)).strftime("%d/%m/%Y"),
            "location": "Pintu A", "related_event": self.event.pk,
            "pickup_option": "ambil sendiri", "details": "Tertutup",
        }
        data.update(extra)
        return {k: v for k, v in data.items() if v is not None}

    def make_report(self, **extra):
        data = {
            "reported_by": self.owner, "food_name": "Roti", "food_portion": 3,
            "best_before": timezone.now() + timedelta(days=1), "location": "Depok",
            "event": "Acara lama", "pickup_option": "ambil sendiri", "details": "Utuh",
            "picture": make_image("lama.png"),
        }
        data.update(extra)
        return Report.objects.create(**data)

    def url(self, name, **kwargs):
        return reverse(f"food_waste_reporting:{name}", kwargs=kwargs)

    def files(self):
        return {"picture": make_image()}


class ReportModelExtraTests(ReportBase):
    def test_event_label_legacy_and_linked(self):
        self.assertEqual(self.make_report().event_label, "Acara lama")
        linked = self.make_report(related_event=self.event)
        self.assertEqual(linked.event_label, "Bazar Kampus")

    def test_pk_is_uuid_and_ordering_newest_first(self):
        first = self.make_report(food_name="Pertama")
        second = self.make_report(food_name="Kedua")
        self.assertEqual(len(str(first.pk)), 36)
        self.assertEqual(list(self.owner.reports.all()), [second, first])

    def test_deleting_user_cascades_reports(self):
        self.make_report()
        self.owner.delete()
        self.assertEqual(Report.objects.count(), 0)


class ReportFormExtraTests(ReportBase):
    def test_valid(self):
        form = ReportForm(self.form_data(), self.files())
        self.assertTrue(form.is_valid(), form.errors)

    def test_required_fields(self):
        for field in ["food_name", "food_portion", "best_before", "location",
                      "pickup_option", "details", "picture", "related_event"]:
            with self.subTest(field=field):
                form = ReportForm(self.form_data(**{field: ""}))
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_best_before_is_aware_and_parsed(self):
        form = ReportForm(self.form_data(best_before="31/12/2027"), self.files())
        self.assertTrue(form.is_valid(), form.errors)
        value = form.cleaned_data["best_before"]
        self.assertTrue(timezone.is_aware(value))
        self.assertEqual((value.day, value.month, value.year), (31, 12, 2027))

    def test_best_before_datetime_local_format(self):
        form = ReportForm(self.form_data(best_before="2027-12-31T14:30"), self.files())
        self.assertTrue(form.is_valid(), form.errors)

    def test_best_before_garbage_rejected(self):
        form = ReportForm(self.form_data(best_before="bukan tanggal"))
        self.assertFalse(form.is_valid())
        self.assertIn("best_before", form.errors)

    def test_invalid_pickup_option_and_portion(self):
        self.assertIn("pickup_option",
                      ReportForm(self.form_data(pickup_option="xxx")).errors)
        for value in ["abc", -1]:
            with self.subTest(value=value):
                self.assertFalse(ReportForm(self.form_data(food_portion=value)).is_valid())

    def test_picture_not_an_image(self):
        fake = SimpleUploadedFile("a.txt", b"bukan gambar", content_type="text/plain")
        form = ReportForm(self.form_data(), {"picture": fake})
        self.assertFalse(form.is_valid())
        self.assertIn("picture", form.errors)

    def test_picture_required(self):
        form = ReportForm(self.form_data())
        self.assertFalse(form.is_valid())
        self.assertIn("picture", form.errors)

    def test_picture_too_large(self):
        form = ReportForm(self.form_data(), {"picture": make_big_image()})
        self.assertFalse(form.is_valid())
        self.assertIn("picture", form.errors)
        self.assertIn("5 MB", str(form.errors["picture"]))

class ShowReportsTests(ReportBase):
    def test_renders_with_context(self):
        self.client.force_login(self.owner)
        res = self.client.get(self.url("show_reports"))
        self.assertEqual(res.status_code, 200)
        self.assertIn("form", res.context)


class GetReportsJsonFilterTests(ReportBase):
    def get(self, query=""):
        return self.client.get(self.url("get_reports_json") + query).json()["reports"]

    def setUp(self):
        self.client.force_login(self.owner)

    def test_search_by_name(self):
        self.make_report(food_name="Roti Bakar")
        self.assertEqual(len(self.get("?name=Bakar")), 1)
        self.assertEqual(self.get("?name=zzz"), [])

    def test_only_own_reports(self):
        mine = self.make_report()
        self.make_report(reported_by=self.other)
        self.assertEqual([r["id"] for r in self.get()], [str(mine.pk)])

    def test_event_fields(self):
        self.make_report(related_event=self.event)
        item = self.get()[0]
        self.assertEqual(item["event"], "Bazar Kampus")
        self.assertEqual(item["related_event_id"], self.event.pk)

    def test_picture_key_present(self):
        self.make_report()
        self.assertIn("picture", self.get()[0])


class CreateReportAjaxExtraTests(ReportBase):
    def test_get_not_allowed(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.url("create_report_ajax")).status_code, 405)

    def test_invalid_returns_400_and_creates_nothing(self):
        self.client.force_login(self.owner)
        res = self.client.post(self.url("create_report_ajax"),
                               self.form_data(food_name=""))
        self.assertEqual(res.status_code, 400)
        self.assertIn("food_name", res.json()["errors"])
        self.assertEqual(Report.objects.count(), 0)

    def test_create_with_picture_upload(self):
        self.client.force_login(self.owner)
        res = self.client.post(self.url("create_report_ajax"),
                               self.form_data(picture=make_image()))
        self.assertEqual(res.status_code, 201)
        self.assertTrue(Report.objects.get(pk=res.json()["pk"]).picture)


class ReportDetailTests(ReportBase):
    def test_owner_sees_detail(self):
        report = self.make_report()
        self.client.force_login(self.owner)
        res = self.client.get(self.url("view_report_detail", report_id=report.pk))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Roti")

    def test_other_user_404_and_unknown_uuid_404(self):
        report = self.make_report()
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.get(self.url("view_report_detail", report_id=report.pk)).status_code, 404)
        self.assertEqual(
            self.client.get(self.url("view_report_detail", report_id=uuid.uuid4())).status_code, 404)

    def test_anonymous_redirected(self):
        report = self.make_report()
        res = self.client.get(self.url("view_report_detail", report_id=report.pk))
        self.assertEqual(res.status_code, 302)


class EditReportTests(ReportBase):
    def setUp(self):
        self.report = self.make_report()
        self.edit_url = self.url("edit_report", report_id=self.report.pk)

    def test_anonymous_redirected(self):
        self.assertEqual(self.client.get(self.edit_url).status_code, 302)

    def test_get_prefill_json(self):
        self.client.force_login(self.owner)
        res = self.client.get(self.edit_url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["food_name"], "Roti")
        self.assertNotIn("picture", res.json())

    def test_post_updates_and_links_event(self):
        self.client.force_login(self.owner)
        res = self.client.post(self.edit_url,
                            self.form_data(food_name="Nama Baru", picture=make_image()))
        self.assertEqual(res.status_code, 200, res.content)
        self.report.refresh_from_db()
        self.assertEqual(self.report.food_name, "Nama Baru")
        self.assertEqual(self.report.related_event, self.event)
        self.assertEqual(self.report.event, "Bazar Kampus") 

    def test_post_invalid_400_and_unchanged(self):
        self.client.force_login(self.owner)
        res = self.client.post(self.edit_url, self.form_data(food_name=""))
        self.assertEqual(res.status_code, 400)
        self.report.refresh_from_db()
        self.assertEqual(self.report.food_name, "Roti")

    def test_other_user_404_get_and_post(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.edit_url).status_code, 404)
        self.assertEqual(self.client.post(self.edit_url, self.form_data()).status_code, 404)

    def test_owner_cannot_be_changed(self):
        self.client.force_login(self.owner)
        self.client.post(self.edit_url, self.form_data(reported_by=self.other.pk))
        self.report.refresh_from_db()
        self.assertEqual(self.report.reported_by, self.owner)


class DeleteReportTests(ReportBase):
    def setUp(self):
        self.report = self.make_report(related_event=self.event)
        self.delete_url = self.url("delete_report", report_id=self.report.pk)

    def test_anonymous_redirected_and_kept(self):
        self.assertEqual(self.client.post(self.delete_url).status_code, 302)
        self.assertTrue(Report.objects.filter(pk=self.report.pk).exists())

    def test_get_not_allowed(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.delete_url).status_code, 405)

    def test_owner_deletes_and_event_stays(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(self.delete_url).status_code, 200)
        self.assertFalse(Report.objects.filter(pk=self.report.pk).exists())
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())

    def test_other_user_404_and_data_kept(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.delete_url).status_code, 404)
        self.assertTrue(Report.objects.filter(pk=self.report.pk).exists())

@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ReportEventIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.participant = User.objects.create_user("report-participant")
        cls.eo = User.objects.create_user("report-eo")
        cls.eo.groups.add(Group.objects.get_or_create(name="EO")[0])
        cls.staff = User.objects.create_user("report-reviewer", is_staff=True)
        cls.event = Event.objects.create(
            name="Festival Kampus",
            event_date=timezone.now() + timedelta(days=2),
            location="Balairung UI",
            description="Acara kampus",
            created_by=cls.eo,
        )

    def form_data(self, **extra):
        data = {
            "food_name": "Nasi Kotak", "food_portion": 5,
            "best_before": (timezone.localdate() + timedelta(days=3)).strftime("%d/%m/%Y"),
            "location": "Dekat pintu A", "related_event": self.event.pk,
            "pickup_option": "ambil sendiri", "details": "Masih tertutup",
        }
        data.update(extra)
        return data

    def make_report(self, **extra):
        data = {
            "reported_by": self.participant, "food_name": "Roti lama", "food_portion": 3,
            "best_before": timezone.now() + timedelta(days=1), "location": "Depok",
            "event": "Nama acara lama", "pickup_option": "ambil sendiri",
            "details": "Utuh", "picture": "https://example.com/food.jpg",
        }
        data.update(extra)
        return Report.objects.create(**data)

    def test_form_renders_existing_event_as_required_dropdown(self):
        form = ReportForm()
        self.assertInHTML(
            f'<option value="{self.event.pk}">Festival Kampus</option>',
            str(form["related_event"]),
        )
        self.assertTrue(form.fields["related_event"].required)
        self.assertNotIn("event", form.fields)

    def test_participant_can_submit_report_for_existing_event(self):
        self.client.force_login(self.participant)
        response = self.client.post(
            reverse("food_waste_reporting:create_report_ajax"),
            self.form_data(picture=make_image(), reported_by=self.staff.pk, event="Forged text"),
        )
        self.assertEqual(response.status_code, 201)
        report = Report.objects.get(pk=response.json()["pk"])
        self.assertEqual(report.reported_by, self.participant)
        self.assertEqual(report.related_event, self.event)
        self.assertEqual(report.event, self.event.name)
        self.assertTrue(report.review.is_pending)

    def test_eo_without_staff_can_submit_but_not_open_report_management(self):
        self.client.force_login(self.eo)
        response = self.client.post(
            reverse("food_waste_reporting:create_report_ajax"), self.form_data(picture=make_image())
        )
        self.assertEqual(response.status_code, 201)
        self.assertFalse(self.eo.is_staff)
        self.assertEqual(
            self.client.get(reverse("food_waste_management:show_management")).status_code,
            403,
        )

    def test_missing_invalid_or_deleted_event_is_rejected(self):
        self.client.force_login(self.participant)
        for event_value in ("", "not-an-id", self.event.pk + 999):
            with self.subTest(event_value=event_value):
                response = self.client.post(
                    reverse("food_waste_reporting:create_report_ajax"),
                    self.form_data(related_event=event_value),
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn("related_event", response.json()["errors"])
        old_event_id = self.event.pk
        self.event.delete()
        response = self.client.post(
            reverse("food_waste_reporting:create_report_ajax"),
            self.form_data(related_event=old_event_id),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Report.objects.count(), 0)

    def test_no_event_does_not_accept_arbitrary_legacy_text(self):
        data = self.form_data(event="Nama bebas")
        del data["related_event"]
        form = ReportForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("related_event", form.errors)

    def test_form_commit_false_retains_event_snapshot(self):
        form = ReportForm(self.form_data(), {"picture": make_image()})
        self.assertTrue(form.is_valid(), form.errors)
        report = form.save(commit=False)
        self.assertTrue(report._state.adding)
        self.assertEqual(report.event, "Festival Kampus")
        self.assertEqual(report.related_event, self.event)
        self.assertFalse(Report.objects.exists())

    def test_report_json_preserves_legacy_names_and_shows_linked_current_names(self):
        legacy = self.make_report()
        linked = self.make_report(event="Original snapshot", related_event=self.event)
        self.make_report(reported_by=self.eo, food_name="Other account")
        self.event.name = "Festival Baru"
        self.event.save()
        self.client.force_login(self.participant)
        response = self.client.get(reverse("food_waste_reporting:get_reports_json"))
        reports = {row["id"]: row for row in response.json()["reports"]}
        self.assertEqual(len(reports), 2)
        self.assertEqual(reports[str(legacy.pk)]["event"], "Nama acara lama")
        self.assertIsNone(reports[str(legacy.pk)]["related_event_id"])
        self.assertEqual(reports[str(linked.pk)]["event"], "Festival Baru")
        self.assertEqual(reports[str(linked.pk)]["related_event_id"], self.event.pk)
        linked.refresh_from_db()
        self.assertEqual(linked.event, "Original snapshot")

    def test_anonymous_cannot_create_or_list_personal_reports(self):
        for route in ("show_reports", "get_reports_json"):
            response = self.client.get(reverse(f"food_waste_reporting:{route}"))
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("authentication:login"), response.url)
        self.assertEqual(
            self.client.post(
                reverse("food_waste_reporting:create_report_ajax"), self.form_data()
            ).status_code, 302,
        )
        self.assertEqual(Report.objects.count(), 0)

    def test_linked_event_cannot_be_deleted_and_report_is_retained(self):
        report = self.make_report(related_event=self.event)
        with self.assertRaises(ProtectedError):
            self.event.delete()
        self.assertTrue(Report.objects.filter(pk=report.pk).exists())
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())

    def test_discovery_search_matches_linked_and_legacy_events(self):
        legacy = self.make_report()
        linked = self.make_report(event="Snapshot not searched", related_event=self.event)
        self.assertQuerySetEqual(
            DiscoveryReport.objects.cari(acara="acara lama"), [legacy.pk],
            transform=lambda report: report.pk,
        )
        self.assertQuerySetEqual(
            DiscoveryReport.objects.cari(acara="festival"), [linked.pk],
            transform=lambda report: report.pk,
        )
        self.assertFalse(DiscoveryReport.objects.cari(acara="Snapshot").exists())

    def test_management_search_and_detail_show_current_linked_event(self):
        legacy = self.make_report()
        linked = self.make_report(event="Snapshot not searched", related_event=self.event)
        for report in (legacy, linked):
            report.review.accept(self.staff)
        self.client.force_login(self.staff)
        response = self.client.get(
            reverse("food_waste_management:handling"), {"q": "festival"}
        )
        self.assertEqual([r.report_id for r in response.context["page_obj"]], [linked.pk])
        response = self.client.get(
            reverse("food_waste_management:handling"), {"q": "acara lama"}
        )
        self.assertEqual([r.report_id for r in response.context["page_obj"]], [legacy.pk])
        response = self.client.get(
            reverse("food_waste_management:detail", kwargs={"report_id": linked.pk})
        )
        self.assertContains(response, "Festival Kampus")
        self.assertNotContains(response, "Snapshot not searched")

    def test_detail_keeps_legacy_event_name(self):
        legacy = self.make_report()
        self.client.force_login(self.participant)
        response = self.client.get(
            reverse("food_waste_reporting:view_report_detail", kwargs={"report_id": legacy.pk})
        )
        self.assertContains(response, "Nama acara lama")


class ReportEventMigrationTests(TransactionTestCase):
    """Exercise an actual schema upgrade and rollback, not just model mocks."""

    migrate_from = [("food_waste_reporting", "0003_alter_report_pickup_option")]
    migrate_to = [("food_waste_reporting", "0004_report_related_event")]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        self.latest_targets = executor.loader.graph.leaf_nodes()
        executor.migrate(self.migrate_from)
        self.old_apps = executor.loader.project_state(self.migrate_from).apps

    def tearDown(self):
        # Always restore the complete schema, even after a failed assertion.
        MigrationExecutor(connection).migrate(self.latest_targets)
        super().tearDown()

    def test_upgrade_and_rollback_keep_legacy_reports_and_snapshot_names(self):
        User = self.old_apps.get_model("auth", "User")
        user = User.objects.create(username="legacy-report-owner")
        OldReport = self.old_apps.get_model("food_waste_reporting", "Report")
        report_values = dict(
            reported_by_id=user.pk, food_name="Legacy food", food_portion=2,
            best_before=timezone.now() + timedelta(days=1), location="Depok",
            event="Acara lama bebas 2024", pickup_option="ambil sendiri",
            details="Original details", picture="https://example.com/legacy.jpg",
        )
        legacy = OldReport.objects.create(**report_values)
        original_time = legacy.created_at
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        new_apps = executor.loader.project_state(self.migrate_to).apps
        NewReport = new_apps.get_model("food_waste_reporting", "Report")
        preserved = NewReport.objects.get(pk=legacy.pk)
        self.assertEqual(preserved.event, "Acara lama bebas 2024")
        self.assertIsNone(preserved.related_event_id)
        self.assertEqual(preserved.reported_by_id, user.pk)
        self.assertEqual(preserved.created_at, original_time)
        EventModel = new_apps.get_model("event_management", "Event")
        event = EventModel.objects.create(
            name="Acara baru", event_date=timezone.now(), description="New event",
            location="Depok", created_by_id=user.pk,
        )
        report_values["event"] = event.name
        new_report = NewReport.objects.create(related_event_id=event.pk, **report_values)
        MigrationExecutor(connection).migrate(self.migrate_from)
        rolled_back = OldReport.objects.get(pk=legacy.pk)
        self.assertEqual(rolled_back.event, "Acara lama bebas 2024")
        self.assertEqual(rolled_back.details, "Original details")
        self.assertEqual(OldReport.objects.get(pk=new_report.pk).event, "Acara baru")
        self.assertEqual(OldReport.objects.count(), 2)
