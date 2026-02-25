"""Campaign sending logic. Runs synchronously for now; Celery-ready."""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Context, Template
from django.utils import timezone

from apps.customers.models import Customer

from .models import Campaign, CampaignRecipient, Subscriber

logger = logging.getLogger(__name__)


def _build_unsubscribe_url(email):
    """Return absolute unsubscribe URL for an email address."""
    site_url = getattr(settings, "SITE_URL", "https://smilememorytravel.com").rstrip(
        "/"
    )
    try:
        sub = Subscriber.objects.get(email=email, is_active=True)
        lang = sub.language or "th"
        return f"{site_url}/{'th' if lang == 'th' else 'en'}/newsletter/unsubscribe/{sub.unsubscribe_token}/"
    except Subscriber.DoesNotExist:
        return f"{site_url}/th/newsletter/unsubscribe/"


def _collect_recipients(campaign):
    """Return list of (email, language, customer_or_None) deduped by email."""
    seen = set()
    recipients = []

    # 1. Customers with marketing opt-in
    customer_qs = Customer.objects.filter(marketing_opt_in=True).select_related(
        "subscriber"
    )
    if not campaign.send_to_all_opted_in and campaign.customer_tags:
        from django.db.models import Q

        tag_list = [t.strip() for t in campaign.customer_tags.split(",") if t.strip()]
        if tag_list:
            q = Q()
            for tag in tag_list:
                q |= Q(tags__icontains=tag)
            customer_qs = customer_qs.filter(q)

    for customer in customer_qs:
        if customer.email not in seen:
            lang = "th"
            if hasattr(customer, "subscriber") and customer.subscriber:
                lang = customer.subscriber.language or "th"
            seen.add(customer.email)
            recipients.append((customer.email, lang, customer))

    # 2. Active Subscribers whose email is NOT already covered by a customer
    for sub in Subscriber.objects.filter(is_active=True).exclude(email__in=seen):
        seen.add(sub.email)
        recipients.append((sub.email, sub.language or "th", None))

    return recipients


def send_campaign(campaign_id, sent_by=None):
    """Send a campaign to all opted-in customers + active subscribers."""
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

    campaign.status = Campaign.Status.SENDING
    campaign.sent_by = sent_by
    campaign.save(update_fields=["status", "sent_by"])

    all_recipients = _collect_recipients(campaign)
    campaign.total_recipients = len(all_recipients)
    campaign.save(update_fields=["total_recipients"])

    # Pre-create CampaignRecipient rows for customers (tracking)
    for email, lang, customer in all_recipients:
        if customer:
            CampaignRecipient.objects.get_or_create(
                campaign=campaign, customer=customer
            )

    body_html_tpl = campaign.get_effective_body_html()
    body_text = campaign.body_text or (
        campaign.template.body_text if campaign.template else ""
    )

    sent_count = 0
    failed_count = 0

    for email, lang, customer in all_recipients:
        subject = _get_subject(campaign, lang)
        unsubscribe_url = _build_unsubscribe_url(email)

        ctx_dict = {
            "customer": customer,
            "email": email,
            "site_name": settings.SITE_NAME,
            "site_url": getattr(settings, "SITE_URL", "https://smilememorytravel.com"),
            "unsubscribe_url": unsubscribe_url,
        }

        try:
            rendered_html = Template(body_html_tpl).render(Context(ctx_dict))

            msg = EmailMultiAlternatives(
                subject=subject,
                body=body_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            msg.attach_alternative(rendered_html, "text/html")
            msg.extra_headers = {
                "List-Unsubscribe": f"<{unsubscribe_url}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            }
            msg.send(fail_silently=False)

            # Update recipient tracking row if customer-linked
            if customer:
                CampaignRecipient.objects.filter(
                    campaign=campaign, customer=customer
                ).update(
                    status=CampaignRecipient.DeliveryStatus.SENT,
                    sent_at=timezone.now(),
                )
            sent_count += 1
        except Exception as exc:
            if customer:
                CampaignRecipient.objects.filter(
                    campaign=campaign, customer=customer
                ).update(
                    status=CampaignRecipient.DeliveryStatus.FAILED,
                    error_message=str(exc)[:500],
                )
            failed_count += 1
            logger.error("Failed to send campaign to %s: %s", email, exc)

    campaign.status = Campaign.Status.SENT
    campaign.sent_at = timezone.now()
    campaign.total_sent = sent_count
    campaign.total_failed = failed_count
    campaign.save()

    logger.info(
        "Campaign '%s' sent: %d success, %d failed / %d total",
        campaign.name,
        sent_count,
        failed_count,
        campaign.total_recipients,
    )


def _get_subject(campaign, lang):
    """Return localized subject for the campaign."""
    if lang == "th":
        if campaign.template and campaign.template.subject_th:
            return campaign.template.subject_th
        if campaign.subject_th:
            return campaign.subject_th
    if campaign.template:
        return campaign.template.subject
    return campaign.subject
