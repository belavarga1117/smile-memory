import uuid

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.customers.models import Customer


class EmailTemplate(TimeStampedModel):
    """Reusable email template for campaigns."""

    name = models.CharField(
        max_length=200, help_text="Internal name e.g. 'Monthly Newsletter'"
    )
    subject = models.CharField(max_length=300)
    subject_th = models.CharField(max_length=300, blank=True)
    body_html = models.TextField(
        help_text="HTML email body. Use {{ customer.first_name }}, {{ unsubscribe_url }} as placeholders."
    )
    body_text = models.TextField(blank=True, help_text="Plain text fallback")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Campaign(TimeStampedModel):
    """Email marketing campaign."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        SENDING = "sending", "Sending"
        SENT = "sent", "Sent"
        CANCELLED = "cancelled", "Cancelled"

    name = models.CharField(max_length=200)
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaigns",
    )

    # Direct content (if not using template)
    subject = models.CharField(max_length=300, blank=True)
    subject_th = models.CharField(max_length=300, blank=True)
    body_html = models.TextField(blank=True)
    body_text = models.TextField(blank=True)

    # Targeting
    send_to_all_opted_in = models.BooleanField(
        default=True,
        help_text="Send to all customers with marketing opt-in",
    )
    customer_tags = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated tags to filter recipients, e.g. 'japan-interest,repeat-customer'",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_campaigns",
    )

    # Stats
    total_recipients = models.PositiveIntegerField(default=0)
    total_sent = models.PositiveIntegerField(default=0)
    total_failed = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def get_effective_subject(self):
        if self.template:
            return self.template.subject
        return self.subject

    def get_effective_body_html(self):
        if self.template:
            return self.template.body_html
        return self.body_html

    def get_recipients(self):
        """Return queryset of customers to receive this campaign."""
        qs = Customer.objects.filter(marketing_opt_in=True)
        if not self.send_to_all_opted_in and self.customer_tags:
            tag_list = [t.strip() for t in self.customer_tags.split(",") if t.strip()]
            if tag_list:
                from django.db.models import Q

                q = Q()
                for tag in tag_list:
                    q |= Q(tags__icontains=tag)
                qs = qs.filter(q)
        return qs


class CampaignRecipient(TimeStampedModel):
    """Tracks individual email delivery per campaign."""

    class DeliveryStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="recipients",
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="campaign_emails",
    )
    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["campaign", "customer"]

    def __str__(self):
        return f"{self.campaign.name} → {self.customer.email}"


class Subscriber(TimeStampedModel):
    """Newsletter subscriber — may or may not be a customer.

    Footer/standalone signup creates Subscriber first,
    then links to Customer if email matches.
    """

    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True)
    customer = models.OneToOneField(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscriber",
    )
    source = models.CharField(
        max_length=100,
        blank=True,
        help_text="Where they subscribed from, e.g. 'footer', 'homepage', 'inquiry'",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        status = "active" if self.is_active else "unsubscribed"
        return f"{self.email} ({status})"
