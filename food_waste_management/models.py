from django.conf import settings
from django.db import models
from django.utils import timezone


class FoodWasteManagement(models.Model):
    """Model awal (placeholder). Belum dipakai fitur apa pun."""
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ReviewTransitionError(ValueError):
    """Dilempar saat perubahan status tidak diizinkan oleh alur verifikasi."""


class ReportReviewQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(verification_status=ReportReview.Verification.PENDING)

    def accepted(self):
        return self.filter(verification_status=ReportReview.Verification.ACCEPTED)

    def rejected(self):
        return self.filter(verification_status=ReportReview.Verification.REJECTED)


class ReportReview(models.Model):
    """Hasil verifikasi dan penanganan sebuah Report (1 laporan = 1 review).

    Dibuat otomatis (lihat signals.py) saat Report dibuat, sehingga modul lain
    (mis. Discovery) cukup memfilter lewat relasi `report.review`.
    """

    class Verification(models.TextChoices):
        PENDING = "menunggu", "Menunggu"
        ACCEPTED = "diterima", "Diterima"
        REJECTED = "ditolak", "Ditolak"

    class Handling(models.TextChoices):
        NOT_STARTED = "belum_diproses", "Belum Diproses"
        AWAITING_PICKUP = "menunggu_penjemputan", "Menunggu Penjemputan"
        CHECKED = "sudah_diperiksa", "Sudah Diperiksa"
        DONE = "selesai", "Selesai"

    class FollowUp(models.TextChoices):
        NONE = "", "Belum Ditentukan"
        SELL = "dijual", "Dijual"
        SHARE = "dibagikan", "Dibagikan"
        PROCESS = "diolah", "Diolah"

    # Urutan penanganan; hanya boleh maju satu langkah.
    HANDLING_ORDER = [
        Handling.NOT_STARTED,
        Handling.AWAITING_PICKUP,
        Handling.CHECKED,
        Handling.DONE,
    ]
    MAX_REASON_LENGTH = 500

    report = models.OneToOneField(
        "food_waste_reporting.Report",
        on_delete=models.CASCADE,
        related_name="review",
    )
    verification_status = models.CharField(
        max_length=20,
        choices=Verification.choices,
        default=Verification.PENDING,
        db_index=True,
    )
    rejection_reason = models.TextField(blank=True, default="")
    handling_status = models.CharField(
        max_length=30,
        choices=Handling.choices,
        default=Handling.NOT_STARTED,
    )
    follow_up = models.CharField(
        max_length=20,
        choices=FollowUp.choices,
        blank=True,
        default="",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_reports",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ReportReviewQuerySet.as_manager()

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.report.food_name} ({self.get_verification_status_display()})"

    # ----- properti bantu untuk template -----
    @property
    def is_pending(self):
        return self.verification_status == self.Verification.PENDING

    @property
    def is_accepted(self):
        return self.verification_status == self.Verification.ACCEPTED

    @property
    def is_rejected(self):
        return self.verification_status == self.Verification.REJECTED

    @property
    def next_handling(self):
        """Nilai status penanganan berikutnya, atau None bila tidak ada."""
        if not self.is_accepted:
            return None
        order = [str(s.value) for s in self.HANDLING_ORDER]
        index = order.index(self.handling_status)
        return order[index + 1] if index + 1 < len(order) else None

    @property
    def next_handling_label(self):
        nxt = self.next_handling
        return self.Handling(nxt).label if nxt else ""

    @property
    def can_set_follow_up(self):
        return self.is_accepted and self.handling_status == self.Handling.CHECKED

    # ----- transisi status -----
    def _stamp(self, user):
        self.reviewed_by = user
        self.reviewed_at = timezone.now()

    def accept(self, user):
        if not self.is_pending:
            raise ReviewTransitionError("Laporan ini sudah diverifikasi.")
        self.verification_status = self.Verification.ACCEPTED
        self.handling_status = self.Handling.AWAITING_PICKUP
        self.rejection_reason = ""
        self._stamp(user)
        self.save()

    def reject(self, user, reason):
        if not self.is_pending:
            raise ReviewTransitionError("Laporan ini sudah diverifikasi.")
        reason = (reason or "").strip()
        if not reason:
            raise ReviewTransitionError("Alasan penolakan wajib diisi.")
        if len(reason) > self.MAX_REASON_LENGTH:
            raise ReviewTransitionError(
                f"Alasan penolakan maksimal {self.MAX_REASON_LENGTH} karakter."
            )
        self.verification_status = self.Verification.REJECTED
        self.rejection_reason = reason
        self._stamp(user)
        self.save()

    def set_handling(self, new_status):
        if not self.is_accepted:
            raise ReviewTransitionError(
                "Status penanganan hanya bisa diubah untuk laporan yang sudah diterima."
            )
        if new_status != self.next_handling:
            raise ReviewTransitionError(
                "Status penanganan harus berurutan dan tidak bisa dimundurkan."
            )
        if new_status == self.Handling.DONE and not self.follow_up:
            raise ReviewTransitionError(
                "Tentukan tindak lanjut sebelum menandai laporan selesai."
            )
        self.handling_status = new_status
        self.save()

    def set_follow_up(self, value):
        if not self.can_set_follow_up:
            raise ReviewTransitionError(
                "Tindak lanjut hanya bisa ditentukan setelah makanan diperiksa "
                "dan sebelum laporan selesai."
            )
        allowed = {c for c, _ in self.FollowUp.choices if c}
        if value not in allowed:
            raise ReviewTransitionError("Pilihan tindak lanjut tidak valid.")
        self.follow_up = value
        self.save()