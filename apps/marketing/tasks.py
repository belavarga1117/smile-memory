"""Campaign sending logic. Runs synchronously for now; use Celery task in production."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, Template
from django.utils import timezone

from .models import Campaign, CampaignRecipient

logger = logging.getLogger(__name__)


def send_campaign(campaign_id, sent_by=None):
    """Send a campaign to all its recipients."""
    try:
        campaign = Campaign.objects.get(pk=campaign_id)
    except Campaign.DoesNotExist:
        logger.error("Campaign %s not found", campaign_id)
        return

    if campaign.status not in (Campaign.Status.DRAFT, Campaign.Status.SCHEDULED):
        logger.warning(
            "Campaign %s is not in sendable state: %s", campaign_id, campaign.status
        )
        return

    # Mark as sending
    campaign.status = Campaign.Status.SENDING
    campaign.sent_by = sent_by
    campaign.save(update_fields=["status", "sent_by"])

    # Get recipients
    recipients = campaign.get_recipients()
    campaign.total_recipients = recipients.count()
    campaign.save(update_fields=["total_recipients"])

    # Create recipient records
    for customer in recipients:
        CampaignRecipient.objects.get_or_create(
            campaign=campaign,
            customer=customer,
        )

    # Get email content
    subject = campaign.get_effective_subject()
    body_html = campaign.get_effective_body_html()
    body_text = (
        campaign.body_text or campaign.template.body_text if campaign.template else ""
    )

    sent_count = 0
    failed_count = 0

    for recipient in CampaignRecipient.objects.filter(
        campaign=campaign, status=CampaignRecipient.DeliveryStatus.PENDING
    ).select_related("customer"):
        customer = recipient.customer

        try:
            # Render template with customer context
            html_template = Template(body_html)
            context = Context(
                {
                    "customer": customer,
                    "site_name": settings.SITE_NAME,
                    "unsubscribe_url": f"/newsletter/unsubscribe/{customer.subscriber.unsubscribe_token}/"
                    if hasattr(customer, "subscriber") and customer.subscriber
                    else "/newsletter/unsubscribe/",
                }
            )
            rendered_html = html_template.render(context)

            send_mail(
                subject=subject,
                message=body_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[customer.email],
                html_message=rendered_html,
                fail_silently=False,
            )
            recipient.status = CampaignRecipient.DeliveryStatus.SENT
            recipient.sent_at = timezone.now()
            sent_count += 1
        except Exception as e:
            recipient.status = CampaignRecipient.DeliveryStatus.FAILED
            recipient.error_message = str(e)[:500]
            failed_count += 1
            logger.error("Failed to send to %s: %s", customer.email, e)

        recipient.save()

    # Update campaign stats
    campaign.status = Campaign.Status.SENT
    campaign.sent_at = timezone.now()
    campaign.total_sent = sent_count
    campaign.total_failed = failed_count
    campaign.save()

    logger.info(
        "Campaign '%s' sent: %d success, %d failed out of %d",
        campaign.name,
        sent_count,
        failed_count,
        campaign.total_recipients,
    )
