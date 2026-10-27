from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms

from .models import Profile

INPUT_CLASSES = (
    'tw-w-full tw-rounded-xl tw-border tw-border-solid tw-border-accent-soft tw-bg-white '
    'tw-px-3 tw-py-2 tw-text-ink tw-[font:inherit] focus:tw-outline-none focus:tw-ring-2 focus:tw-ring-accent'
)


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = 'Maksimal 150 karakter. Gunakan huruf, angka, atau @ . + - _'
        self.fields['username'].widget.attrs['placeholder'] = 'Pilih username kamu'
        self.fields['email'].widget.attrs.update(placeholder='nama@email.com', autocomplete='email')
        self.fields['password1'].help_text = 'Minimal 8 karakter; hindari password umum, angka saja, atau yang mirip data pribadimu.'
        self.fields['password1'].widget.attrs['placeholder'] = 'Buat password yang kuat'
        self.fields['password2'].label = 'Konfirmasi password'
        self.fields['password2'].help_text = 'Ketik ulang password yang sama.'
        self.fields['password2'].widget.attrs['placeholder'] = 'Ulangi password kamu'


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('display_name', 'city', 'bio', 'phone', 'line_id')
        widgets = {'bio': forms.Textarea(attrs={'rows': 3})}
        help_texts = {
            'phone': 'Hanya terlihat oleh pengguna yang sudah login.',
            'line_id': 'Hanya terlihat oleh pengguna yang sudah login.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'display_name': 'Nama yang ditampilkan ke pengguna lain',
            'city': 'Depok',
            'bio': 'Ceritakan sedikit tentang dirimu',
            'phone': '081234567890',
            'line_id': 'foodwastey',
        }
        for name, field in self.fields.items():
            field.widget.attrs.update(placeholder=placeholders[name], **{'class': INPUT_CLASSES})

    def clean_city(self):
        # Disimpan rapi agar filter kota tidak terpecah oleh beda kapitalisasi.
        return ' '.join(self.cleaned_data['city'].split()).title()


class DeleteAccountForm(forms.Form):
    confirm_username = forms.CharField(label='Ketik username kamu untuk konfirmasi', max_length=150)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['confirm_username'].widget.attrs.update(
            autocomplete='off', placeholder=user.get_username(), **{'class': INPUT_CLASSES})

    def clean_confirm_username(self):
        value = self.cleaned_data['confirm_username']
        if value != self.user.get_username():
            raise forms.ValidationError('Username tidak cocok.')
        return value

    def clean(self):
        if self.user.is_superuser:
            raise forms.ValidationError('Akun admin tidak bisa dihapus dari halaman ini.')
        return super().clean()
