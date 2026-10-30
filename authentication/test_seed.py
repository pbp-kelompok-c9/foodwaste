import json
import os
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils import timezone

from authentication.management.commands.seed_data import DATA_FILE
from event_management.models import Event
from food_waste_management.models import ReportReview
from food_waste_reporting.models import Report


def run_seed(**kwargs):
    out = StringIO()
    call_command('seed_data', stdout=out, **kwargs)
    return out.getvalue()


class SeedDataTests(TestCase):
    def test_creates_fifty_reports_with_accounts_and_events(self):
        output = run_seed()
        self.assertEqual(Report.objects.count(), 50)
        self.assertEqual(Event.objects.count(), 10)
        self.assertEqual(get_user_model().objects.count(), 10)
        self.assertIn('50 laporan baru', output)

    def test_running_twice_does_not_duplicate(self):
        run_seed()
        output = run_seed()
        self.assertEqual(Report.objects.count(), 50)
        self.assertEqual(Event.objects.count(), 10)
        self.assertIn('0 laporan baru', output)

    def test_roles_and_profiles(self):
        run_seed()
        User = get_user_model()
        self.assertTrue(User.objects.get(username='petugas.foodwastey').is_staff)
        self.assertTrue(User.objects.get(username='bem.fasilkom').groups.filter(name='EO').exists())
        self.assertFalse(User.objects.filter(is_superuser=True).exists())
        self.assertEqual(User.objects.get(username='kevin.wijaya').profile.city, 'Tangerang Selatan')

    def test_reviews_follow_seed_status(self):
        run_seed()
        reviews = ReportReview.objects.all()
        self.assertEqual(reviews.count(), 50)
        self.assertEqual(reviews.filter(verification_status='menunggu').count(), 8)
        self.assertEqual(reviews.filter(verification_status='ditolak').exclude(rejection_reason='').count(), 5)
        accepted = reviews.filter(verification_status='diterima')
        self.assertEqual(accepted.count(), 37)
        self.assertFalse(accepted.filter(handling_status='belum_diproses').exists())
        self.assertFalse(accepted.filter(handling_status='selesai', follow_up='').exists())

    def test_times_are_relative_and_consistent(self):
        run_seed()
        now = timezone.now()
        self.assertFalse(Report.objects.filter(created_at__gt=now).exists())
        for report in Report.objects.select_related('related_event'):
            self.assertGreaterEqual(report.created_at, report.related_event.event_date)
            self.assertGreater(report.best_before, report.created_at)
        # Sebagian makanan masih bisa diambil dan acara mendatang belum punya laporan.
        self.assertTrue(Report.objects.filter(best_before__gt=now, review__verification_status='diterima').exists())
        self.assertTrue(Event.objects.filter(event_date__gt=now, reports__isnull=True).exists())

    def test_password_from_environment(self):
        with mock.patch.dict(os.environ, {'SEED_PASSWORD': 'RahasiaSeed!2026'}):
            run_seed()
        self.assertTrue(get_user_model().objects.get(username='dimas.pratama').check_password('RahasiaSeed!2026'))

    def test_without_password_accounts_cannot_log_in(self):
        with mock.patch.dict(os.environ, {'SEED_PASSWORD': ''}):
            output = run_seed()
        self.assertFalse(get_user_model().objects.get(username='dimas.pratama').has_usable_password())
        self.assertIn('SEED_PASSWORD tidak diisi', output)

    def test_existing_data_is_kept(self):
        User = get_user_model()
        user = User.objects.create_user('dimas.pratama', password='punyaSendiri123')
        run_seed()
        user.refresh_from_db()
        self.assertTrue(user.check_password('punyaSendiri123'))
        self.assertEqual(Report.objects.count(), 50)

    def test_missing_file_raises_error(self):
        with self.assertRaises(CommandError):
            run_seed(file='/tidak/ada/data.json')

    def test_data_file_is_valid_json_with_fifty_reports(self):
        with open(DATA_FILE, encoding='utf-8') as data_file:
            data = json.load(data_file)
        self.assertEqual(len(data['reports']), 50)
