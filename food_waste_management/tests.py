from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from food_waste_management.models import ReportReview, ReviewTransitionError
from food_waste_reporting.models import Report

Verification = ReportReview.Verification
Handling = ReportReview.Handling


class ManagementTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user("panitia", password="pw12345!", is_staff=True)
        cls.peserta = User.objects.create_user("peserta", password="pw12345!")

    def make_report(self, name="Pasta Sisaan", **extra):
        data = dict(
            reported_by=self.peserta,
            food_name=name,
            food_portion=5,
            best_before=timezone.now() + timedelta(hours=3),
            location="PBP Convention Hall",
            event="Wedding",
            pickup_option="ambil sendiri",
            details="Masih hangat",
            picture="https://example.com/pasta.jpg",
        )
        data.update(extra)
        return Report.objects.create(**data)

    def url(self, name, report=None):
        kwargs = {"report_id": report.pk} if report else {}
        return reverse(f"food_waste_management:{name}", kwargs=kwargs)


class ReviewModelTests(ManagementTestBase):
    def test_review_created_automatically_as_pending(self):
        report = self.make_report()
        self.assertEqual(report.review.verification_status, Verification.PENDING)
        self.assertEqual(report.review.handling_status, Handling.NOT_STARTED)

    def test_saving_report_again_does_not_duplicate_review(self):
        report = self.make_report()
        report.food_portion = 9
        report.save()
        self.assertEqual(ReportReview.objects.filter(report=report).count(), 1)

    def test_accept_moves_to_awaiting_pickup(self):
        review = self.make_report().review
        review.accept(self.staff)
        review.refresh_from_db()
        self.assertEqual(review.verification_status, Verification.ACCEPTED)
        self.assertEqual(review.handling_status, Handling.AWAITING_PICKUP)
        self.assertEqual(review.reviewed_by, self.staff)
        self.assertIsNotNone(review.reviewed_at)

    def test_cannot_verify_twice(self):
        review = self.make_report().review
        review.accept(self.staff)
        with self.assertRaises(ReviewTransitionError):
            review.accept(self.staff)
        with self.assertRaises(ReviewTransitionError):
            review.reject(self.staff, "alasan")

    def test_reject_requires_reason(self):
        review = self.make_report().review
        for bad in ("", "   ", None):
            with self.assertRaises(ReviewTransitionError):
                review.reject(self.staff, bad)
        with self.assertRaises(ReviewTransitionError):
            review.reject(self.staff, "x" * (ReportReview.MAX_REASON_LENGTH + 1))
        review.refresh_from_db()
        self.assertTrue(review.is_pending)

    def test_reject_saves_reason(self):
        review = self.make_report().review
        review.reject(self.staff, "  Foto tidak sesuai  ")
        review.refresh_from_db()
        self.assertEqual(review.verification_status, Verification.REJECTED)
        self.assertEqual(review.rejection_reason, "Foto tidak sesuai")

    def test_handling_requires_accepted_report(self):
        review = self.make_report().review
        with self.assertRaises(ReviewTransitionError):
            review.set_handling(Handling.CHECKED)

    def test_handling_must_follow_order(self):
        review = self.make_report().review
        review.accept(self.staff)
        with self.assertRaises(ReviewTransitionError):
            review.set_handling(Handling.DONE)  # lompat langkah
        review.set_handling(Handling.CHECKED)
        with self.assertRaises(ReviewTransitionError):
            review.set_handling(Handling.AWAITING_PICKUP)  # mundur
        with self.assertRaises(ReviewTransitionError):
            review.set_handling("sembarang")

    def test_cannot_finish_without_follow_up(self):
        review = self.make_report().review
        review.accept(self.staff)
        review.set_handling(Handling.CHECKED)
        with self.assertRaises(ReviewTransitionError):
            review.set_handling(Handling.DONE)
        review.set_follow_up("dibagikan")
        review.set_handling(Handling.DONE)
        review.refresh_from_db()
        self.assertEqual(review.handling_status, Handling.DONE)
        self.assertEqual(review.follow_up, "dibagikan")

    def test_follow_up_only_after_checked_and_before_done(self):
        review = self.make_report().review
        with self.assertRaises(ReviewTransitionError):
            review.set_follow_up("dijual")  # belum diterima
        review.accept(self.staff)
        with self.assertRaises(ReviewTransitionError):
            review.set_follow_up("dijual")  # belum diperiksa
        review.set_handling(Handling.CHECKED)
        with self.assertRaises(ReviewTransitionError):
            review.set_follow_up("dibuang")  # nilai tidak valid
        review.set_follow_up("dijual")
        review.set_handling(Handling.DONE)
        with self.assertRaises(ReviewTransitionError):
            review.set_follow_up("diolah")  # sudah selesai, terkunci

    def test_accepted_queryset_for_discovery(self):
        a, b, c = self.make_report("A"), self.make_report("B"), self.make_report("C")
        a.review.accept(self.staff)
        b.review.reject(self.staff, "tidak layak")
        self.assertEqual(list(ReportReview.objects.accepted()), [a.review])
        self.assertEqual(list(Report.objects.filter(review__verification_status="diterima")), [a])
        self.assertEqual(list(ReportReview.objects.pending()), [c.review])
        self.assertEqual(list(ReportReview.objects.rejected()), [b.review])


class AccessControlTests(ManagementTestBase):
    def test_anonymous_redirected_to_login(self):
        report = self.make_report()
        for name in ("show_management", "queue", "handling"):
            response = self.client.get(self.url(name))
            self.assertEqual(response.status_code, 302, name)
            self.assertIn(reverse("authentication:login"), response.url)
        response = self.client.get(self.url("detail", report))
        self.assertEqual(response.status_code, 302)

    def test_non_staff_forbidden(self):
        report = self.make_report()
        self.client.force_login(self.peserta)
        for name in ("show_management", "queue", "handling"):
            self.assertEqual(self.client.get(self.url(name)).status_code, 403, name)
        self.assertEqual(self.client.get(self.url("detail", report)).status_code, 403)

    def test_non_staff_cannot_post_actions(self):
        report = self.make_report()
        self.client.force_login(self.peserta)
        for name in ("accept", "reject", "update_handling", "follow_up"):
            response = self.client.post(self.url(name, report), {"reason": "x"})
            self.assertEqual(response.status_code, 403, name)
        report.review.refresh_from_db()
        self.assertTrue(report.review.is_pending)

    def test_anonymous_cannot_post_actions(self):
        report = self.make_report()
        response = self.client.post(self.url("accept", report))
        self.assertEqual(response.status_code, 302)
        report.review.refresh_from_db()
        self.assertTrue(report.review.is_pending)

    def test_actions_reject_get_requests(self):
        report = self.make_report()
        self.client.force_login(self.staff)
        for name in ("accept", "reject", "update_handling", "follow_up"):
            self.assertEqual(self.client.get(self.url(name, report)).status_code, 405, name)

    def test_staff_can_open_pages(self):
        report = self.make_report()
        self.client.force_login(self.staff)
        for name in ("show_management", "queue", "handling"):
            self.assertEqual(self.client.get(self.url(name)).status_code, 200, name)
        self.assertEqual(self.client.get(self.url("detail", report)).status_code, 200)

    def test_unknown_report_returns_404(self):
        import uuid
        self.client.force_login(self.staff)
        url = reverse("food_waste_management:detail", kwargs={"report_id": uuid.uuid4()})
        self.assertEqual(self.client.get(url).status_code, 404)


class WorkflowViewTests(ManagementTestBase):
    def setUp(self):
        self.client.force_login(self.staff)

    def test_full_flow_through_views(self):
        report = self.make_report()
        self.client.post(self.url("accept", report))
        self.client.post(self.url("update_handling", report), {"handling_status": "sudah_diperiksa"})
        self.client.post(self.url("follow_up", report), {"follow_up": "diolah"})
        response = self.client.post(self.url("update_handling", report),
                                    {"handling_status": "selesai"}, follow=True)
        self.assertEqual(response.status_code, 200)
        review = ReportReview.objects.get(report=report)
        self.assertEqual(review.verification_status, Verification.ACCEPTED)
        self.assertEqual(review.handling_status, Handling.DONE)
        self.assertEqual(review.follow_up, "diolah")

    def test_accept_redirects_back_to_queue_when_requested(self):
        report = self.make_report()
        response = self.client.post(self.url("accept", report), {"next": "queue"})
        self.assertRedirects(response, self.url("queue"))

    def test_next_parameter_cannot_redirect_elsewhere(self):
        report = self.make_report()
        response = self.client.post(self.url("accept", report), {"next": "https://evil.example"})
        self.assertRedirects(response, self.url("detail", report))

    def test_reject_without_reason_keeps_report_pending(self):
        report = self.make_report()
        response = self.client.post(self.url("reject", report), {"reason": ""}, follow=True)
        self.assertContains(response, "Alasan penolakan wajib diisi.")
        report.review.refresh_from_db()
        self.assertTrue(report.review.is_pending)

    def test_reject_with_reason(self):
        report = self.make_report()
        self.client.post(self.url("reject", report), {"reason": "Foto buram"})
        report.review.refresh_from_db()
        self.assertEqual(report.review.verification_status, Verification.REJECTED)
        self.assertEqual(report.review.rejection_reason, "Foto buram")

    def test_invalid_transition_shows_error_message(self):
        report = self.make_report()
        response = self.client.post(self.url("update_handling", report),
                                    {"handling_status": "selesai"}, follow=True)
        self.assertContains(response, "hanya bisa diubah untuk laporan yang sudah diterima")

    def test_queue_lists_only_pending(self):
        pending = self.make_report("Menunggu Aja")
        accepted = self.make_report("Sudah Diterima")
        accepted.review.accept(self.staff)
        response = self.client.get(self.url("queue"))
        self.assertContains(response, pending.food_name)
        self.assertNotContains(response, accepted.food_name)

    def test_handling_lists_only_accepted_and_filters(self):
        pending = self.make_report("Belum Diverifikasi")
        a = self.make_report("Nasi Kotak")
        b = self.make_report("Roti Tawar")
        a.review.accept(self.staff)
        b.review.accept(self.staff)
        b.review.set_handling(Handling.CHECKED)
        response = self.client.get(self.url("handling"))
        self.assertContains(response, "Nasi Kotak")
        self.assertContains(response, "Roti Tawar")
        self.assertNotContains(response, pending.food_name)
        response = self.client.get(self.url("handling"), {"status": "sudah_diperiksa"})
        self.assertContains(response, "Roti Tawar")
        self.assertNotContains(response, "Nasi Kotak")
        response = self.client.get(self.url("handling"), {"q": "nasi"})
        self.assertContains(response, "Nasi Kotak")
        self.assertNotContains(response, "Roti Tawar")

    def test_unknown_status_filter_is_ignored(self):
        report = self.make_report("Nasi Kotak")
        report.review.accept(self.staff)
        response = self.client.get(self.url("handling"), {"status": "<script>"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nasi Kotak")

    def test_summary_counts(self):
        a, b, c = self.make_report("A"), self.make_report("B"), self.make_report("C")
        a.review.accept(self.staff)
        b.review.reject(self.staff, "tidak layak")
        response = self.client.get(self.url("show_management"))
        stats = response.context["stats"]
        self.assertEqual((stats["pending"], stats["accepted"], stats["rejected"]), (1, 1, 1))

    def test_pagination_on_queue(self):
        for i in range(12):
            self.make_report(f"Makanan {i}")
        response = self.client.get(self.url("queue"))
        self.assertEqual(len(response.context["page_obj"]), 10)
        response = self.client.get(self.url("queue"), {"page": 2})
        self.assertEqual(len(response.context["page_obj"]), 2)

    def test_detail_escapes_user_content(self):
        report = self.make_report(food_name="<script>alert(1)</script>")
        response = self.client.get(self.url("detail", report))
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;")

    def test_non_http_picture_is_not_rendered_as_image(self):
        report = self.make_report(picture="javascript:alert(1)")
        response = self.client.get(self.url("detail", report))
        self.assertNotContains(response, "javascript:alert(1)")