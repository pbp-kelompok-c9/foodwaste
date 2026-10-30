import json
import os
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from event_management.models import Event
from food_waste_management.models import ReportReview
from food_waste_reporting.models import Report

DATA_FILE = Path(settings.BASE_DIR) / 'seed' / 'initial_data.json'


class Command(BaseCommand):
    help = (
        'Mengisi database dengan data awal FoodWastey (akun, acara, dan 50 laporan makanan). '
        'Aman dijalankan berulang kali: data yang sudah ada tidak diduplikasi atau diubah.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--file', default=str(DATA_FILE), help='Lokasi file JSON data awal.')

    def handle(self, *args, **options):
        path = Path(options['file'])
        if not path.exists():
            raise CommandError(f'File data awal tidak ditemukan: {path}')
        data = json.loads(path.read_text(encoding='utf-8'))

        # Repo ini publik, jadi password akun contoh tidak disimpan di file data.
        password = os.getenv('SEED_PASSWORD', '')
        # Semua waktu di file data relatif terhadap saat seed, agar data tidak langsung kedaluwarsa.
        now = timezone.now().replace(second=0, microsecond=0)

        with transaction.atomic():
            users, new_users = self._seed_users(data['users'], password)
            events, new_events = self._seed_events(data['events'], users, now)
            new_reports = self._seed_reports(data['reports'], users, events, now)

        self.stdout.write(self.style.SUCCESS(
            f'Seed selesai: {new_users} akun, {new_events} acara, dan {new_reports} laporan baru '
            f'(total laporan sekarang {Report.objects.count()}).'
        ))
        if new_users and not password:
            self.stdout.write(
                'SEED_PASSWORD tidak diisi, sehingga akun contoh dibuat tanpa password yang bisa dipakai login.'
            )

    def _seed_users(self, rows, password):
        User = get_user_model()
        eo_group, _ = Group.objects.get_or_create(name='EO')
        users, created_count = {}, 0
        for row in rows:
            user, created = User.objects.get_or_create(
                username=row['username'],
                defaults={'is_staff': row['role'] == 'staff'},
            )
            if created:
                created_count += 1
                if password:
                    user.set_password(password)
                else:
                    user.set_unusable_password()
                user.save()
                if row['role'] == 'eo':
                    user.groups.add(eo_group)
                # Profil dibuat otomatis oleh signal; cukup lengkapi isinya.
                profile = user.profile
                profile.display_name = row['display_name']
                profile.city = row['city']
                profile.bio = row['bio']
                profile.save()
            users[row['username']] = user
        return users, created_count

    def _seed_events(self, rows, users, now):
        events, created_count = {}, 0
        for row in rows:
            start = (now - timedelta(hours=row['start_hours_ago'])).replace(minute=0)
            event, created = Event.objects.get_or_create(
                name=row['name'],
                created_by=users[row['organizer']],
                defaults={
                    'event_date': start,
                    'description': row['description'],
                    'location': row['location'],
                    'latitude': row['latitude'],
                    'longitude': row['longitude'],
                },
            )
            created_count += created
            events[row['key']] = event
        return events, created_count

    def _seed_reports(self, rows, users, events, now):
        staff = next((user for user in users.values() if user.is_staff), None)
        created_count = 0
        for row in rows:
            event = events[row['event']]
            reported_at = min(event.event_date + timedelta(hours=row['reported_after_hours']), now)
            report, created = Report.objects.get_or_create(
                reported_by=users[row['reporter']],
                related_event=event,
                food_name=row['food_name'],
                defaults={
                    'food_portion': row['food_portion'],
                    'best_before': reported_at + timedelta(hours=row['shelf_life_hours']),
                    'location': row['spot'],
                    'event': event.name,
                    'pickup_option': row['pickup'],
                    'details': row['details'],
                },
            )
            if not created:
                continue
            created_count += 1
            # created_at memakai auto_now_add, jadi waktu lapor diatur lewat update().
            Report.objects.filter(pk=report.pk).update(created_at=reported_at)
            self._apply_review(report, row['review'], staff, reported_at, now)
        return created_count

    def _apply_review(self, report, review, staff, reported_at, now):
        status = review['status']
        if status == ReportReview.Verification.PENDING:
            return
        # Review sudah dibuat oleh signal Food Waste Management saat laporan tersimpan.
        fields = {
            'verification_status': status,
            'reviewed_by': staff,
            'reviewed_at': min(reported_at + timedelta(hours=1), now),
        }
        if status == ReportReview.Verification.REJECTED:
            fields['rejection_reason'] = review['reason']
        else:
            fields['handling_status'] = review.get('handling', ReportReview.Handling.AWAITING_PICKUP)
            fields['follow_up'] = review.get('follow_up', '')
        ReportReview.objects.filter(report=report).update(**fields)
