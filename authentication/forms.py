from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms


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
