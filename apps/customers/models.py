from django.db import models

from apps.core.models import TimeStampedModel


class Customer(TimeStampedModel):
    """Customer record — created from inquiry or newsletter signup."""

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    line_id = models.CharField(max_length=100, blank=True, help_text="LINE ID")

    # Marketing consent
    marketing_opt_in = models.BooleanField(
        default=False, help_text="Agreed to receive marketing emails"
    )
    opted_in_at = models.DateTimeField(null=True, blank=True)

    # Segmentation
    tags = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated tags for segmentation, e.g. 'japan-interest,repeat-customer'",
    )
    notes = models.TextField(blank=True, help_text="Internal notes about this customer")

    # Stats
    total_inquiries = models.PositiveIntegerField(default=0)
    total_bookings = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["marketing_opt_in"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]
