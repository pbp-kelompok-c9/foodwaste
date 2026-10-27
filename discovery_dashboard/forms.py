from django import forms
from .models import PickupClaim


class PickupProofForm(forms.ModelForm):

    class Meta:
        model = PickupClaim
        fields = ["proof_photo"]

    def clean_proof_photo(self):
        foto = self.cleaned_data.get("proof_photo")

        if not foto:
            raise forms.ValidationError(
                "Foto wajib diunggah."
            )

        if foto.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                "Ukuran foto maksimal 5 MB."
            )

        return foto