from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.customers.models import Customer
from apps.tours.models import Tour, TourDeparture


class Inquiry(TimeStampedModel):
    """Booking inquiry — the central booking workflow model.

    Workflow: NEW → CONTACTED → CONFIRMED / REJECTED / CANCELLED
    """

    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        CONFIRMED = "confirmed", "Confirmed"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    # Customer link
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="inquiries"
    )

    # Tour info
    tour = models.ForeignKey(
        Tour, on_delete=models.SET_NULL, null=True, related_name="inquiries"
    )
    departure = models.ForeignKey(
        TourDeparture,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
        help_text="Specific departure date if selected",
    )

    # Traveler details
    num_adults = models.PositiveIntegerField(default=1)
    num_children = models.PositiveIntegerField(default=0)
    num_infants = models.PositiveIntegerField(default=0)
    room_preference = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g. double, twin, single",
    )
    special_requests = models.TextField(blank=True)

    # Contact info (duplicate from customer for convenience)
    contact_name = models.CharField(max_length=200)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=50, blank=True)

    # Marketing
    marketing_opt_in = models.BooleanField(default=False)

    # Workflow
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_inquiries",
        help_text="Admin staff member handling this inquiry",
    )

    # Pricing (filled by admin upon confirmation)
    quoted_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total quoted price",
    )
    deposit_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # Dates
    confirmed_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    # Reference
    reference_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        help_text="Auto-generated booking reference e.g. SM-20260224-001",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Inquiries"
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["customer"]),
            models.Index(fields=["reference_number"]),
        ]

    def __str__(self):
        return f"{self.reference_number} — {self.contact_name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = self._generate_reference()
        super().save(*args, **kwargs)

    def _generate_reference(self):
        from django.utils import timezone

        today = timezone.now().strftime("%Y%m%d")
        last = (
            Inquiry.objects.filter(reference_number__startswith=f"SM-{today}")
            .order_by("-reference_number")
            .first()
        )
        if last and last.reference_number:
            try:
                seq = int(last.reference_number.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"SM-{today}-{seq:03d}"

    @property
    def total_travelers(self):
        return self.num_adults + self.num_children + self.num_infants


class InquiryNote(TimeStampedModel):
    """Internal note on an inquiry — for admin communication trail."""

    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    note = models.TextField()
    is_email_sent = models.BooleanField(
        default=False, help_text="Was this note sent as email to customer?"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on {self.inquiry.reference_number} by {self.author}"
