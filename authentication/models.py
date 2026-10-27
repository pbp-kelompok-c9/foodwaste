from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q

phone_validator = RegexValidator(
    r'^\+?[0-9]{8,15}$',
    'Gunakan 8-15 digit angka, boleh diawali tanda +.',
)


class ProfileQuerySet(models.QuerySet):
    def search(self, query='', city=''):
        profiles = self
        if query:
            profiles = profiles.filter(
                Q(user__username__icontains=query) | Q(display_name__icontains=query)
            )
        if city:
            profiles = profiles.filter(city__iexact=city)
        return profiles

    def cities(self):
        return (self.exclude(city='').order_by('city')
                .values_list('city', flat=True).distinct())


class Profile(models.Model):
    """Data profil pengguna. Kontak hanya ditampilkan ke pengguna yang sudah login."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile'
    )
    display_name = models.CharField('Nama tampilan', max_length=80, blank=True)
    city = models.CharField('Kota', max_length=60, blank=True)
    bio = models.TextField('Tentang saya', max_length=300, blank=True)
    phone = models.CharField('Nomor HP', max_length=16, blank=True, validators=[phone_validator])
    line_id = models.CharField('ID LINE', max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProfileQuerySet.as_manager()

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return f'Profil {self.user.username}'

    @property
    def name(self):
        return self.display_name or self.user.username

    def to_dict(self, include_contact=False):
        data = {
            'username': self.user.username,
            'display_name': self.display_name,
            'name': self.name,
            'city': self.city,
            'bio': self.bio,
            'joined': self.user.date_joined.date().isoformat(),
        }
        if include_contact:
            data.update(phone=self.phone, line_id=self.line_id)
        return data
