"""Tests for marketing campaign sending tasks."""

import pytest
from unittest.mock import patch

from .factories import (
    CustomerFactory,
    CampaignFactory,
    EmailTemplateFactory,
    SubscriberFactory,
)


@pytest.mark.django_db
class TestSendCampaign:
    """Tests for send_campaign() task."""

    def test_send_to_opted_in_customers(self):
        """Campaign sends to all marketing opt-in customers."""
        from apps.marketing.tasks import send_campaign
        from apps.marketing.models import Campaign, CampaignRecipient

        customer1 = CustomerFactory(marketing_opt_in=True)
        customer2 = CustomerFactory(marketing_opt_in=True)
        CustomerFactory(marketing_opt_in=False)  # should not receive

        template = EmailTemplateFactory(
            subject="Test subject",
            body_html="<p>Hello {{ customer.first_name }}</p>",
            body_text="Hello {{ customer.first_name }}",
        )
        campaign = CampaignFactory(
            template=template,
            status=Campaign.Status.DRAFT,
            send_to_all_opted_in=True,
        )

        with patch("apps.marketing.tasks.EmailMultiAlternatives") as mock_email:
            mock_msg = mock_email.return_value
            mock_msg.send.return_value = 1
            send_campaign(campaign.pk)

        campaign.refresh_from_db()
        assert campaign.status == Campaign.Status.SENT
        assert campaign.total_sent >= 2
        # CampaignRecipient rows are created for customers
        recipients = CampaignRecipient.objects.filter(campaign=campaign)
        assert recipients.count() >= 2
        customer_ids = list(recipients.values_list("customer_id", flat=True))
        assert customer1.pk in customer_ids
        assert customer2.pk in customer_ids

    def test_send_to_active_subscribers_only(self):
        """Campaign sends to active subscribers but not inactive ones."""
        from apps.marketing.tasks import send_campaign
        from apps.marketing.models import Campaign

        SubscriberFactory(is_active=True)
        SubscriberFactory(is_active=False)  # should not receive

        template = EmailTemplateFactory()
        campaign = CampaignFactory(
            template=template,
            status=Campaign.Status.DRAFT,
            send_to_all_opted_in=True,
        )

        with patch("apps.marketing.tasks.EmailMultiAlternatives") as mock_email:
            mock_msg = mock_email.return_value
            mock_msg.send.return_value = 1
            send_campaign(campaign.pk)

        campaign.refresh_from_db()
        assert campaign.status == Campaign.Status.SENT
        # Only active subscriber (1) should be counted
        assert campaign.total_sent == 1
        assert campaign.total_recipients == 1

    def test_nonexistent_campaign_logs_error(self):
        """Non-existent campaign ID logs error without crashing."""
        from apps.marketing.tasks import send_campaign

        # Should not raise
        send_campaign(99999)

    def test_already_sent_campaign_skipped(self):
        """Campaign already in SENT status is not re-sent."""
        from apps.marketing.tasks import send_campaign
        from apps.marketing.models import Campaign

        campaign = CampaignFactory(status=Campaign.Status.SENT)

        with patch("apps.marketing.tasks.EmailMultiAlternatives") as mock_email:
            send_campaign(campaign.pk)
            mock_email.assert_not_called()

    def test_tag_filtered_campaign(self):
        """Campaign with customer_tags only sends to matching customers."""
        from apps.marketing.tasks import send_campaign
        from apps.marketing.models import Campaign, CampaignRecipient

        japan_customer = CustomerFactory(marketing_opt_in=True, tags="japan-interest")
        other_customer = CustomerFactory(marketing_opt_in=True, tags="europe-interest")

        template = EmailTemplateFactory()
        campaign = CampaignFactory(
            template=template,
            status=Campaign.Status.DRAFT,
            send_to_all_opted_in=False,
            customer_tags="japan-interest",
        )

        with patch("apps.marketing.tasks.EmailMultiAlternatives") as mock_email:
            mock_msg = mock_email.return_value
            mock_msg.send.return_value = 1
            send_campaign(campaign.pk)

        # Only japan_customer should have a CampaignRecipient row
        assert CampaignRecipient.objects.filter(
            campaign=campaign, customer=japan_customer
        ).exists()
        assert not CampaignRecipient.objects.filter(
            campaign=campaign, customer=other_customer
        ).exists()

    def test_no_duplicate_recipients(self):
        """Customer who is also a subscriber only receives one email."""
        from apps.marketing.tasks import send_campaign
        from apps.marketing.models import Campaign, CampaignRecipient

        customer = CustomerFactory(marketing_opt_in=True)
        # Link subscriber to same customer (same email)
        sub = SubscriberFactory(email=customer.email, is_active=True)
        sub.customer = customer
        sub.save()

        template = EmailTemplateFactory()
        campaign = CampaignFactory(
            template=template, status=Campaign.Status.DRAFT, send_to_all_opted_in=True
        )

        with patch("apps.marketing.tasks.EmailMultiAlternatives") as mock_email:
            mock_msg = mock_email.return_value
            mock_msg.send.return_value = 1
            send_campaign(campaign.pk)

        campaign.refresh_from_db()
        # Email sent exactly once
        assert campaign.total_sent == 1
        # Exactly one CampaignRecipient for this customer
        assert (
            CampaignRecipient.objects.filter(
                campaign=campaign, customer=customer
            ).count()
            == 1
        )


@pytest.mark.django_db
class TestBuildUnsubscribeUrl:
    """Tests for _build_unsubscribe_url helper."""

    def test_returns_url_for_active_subscriber(self):
        from apps.marketing.tasks import _build_unsubscribe_url

        sub = SubscriberFactory(is_active=True, language="th")
        url = _build_unsubscribe_url(sub.email)
        assert str(sub.unsubscribe_token) in url
        assert "/th/" in url

    def test_fallback_url_for_unknown_email(self):
        from apps.marketing.tasks import _build_unsubscribe_url

        url = _build_unsubscribe_url("unknown@example.com")
        assert "newsletter/unsubscribe" in url

    def test_english_subscriber_gets_en_url(self):
        from apps.marketing.tasks import _build_unsubscribe_url

        sub = SubscriberFactory(is_active=True, language="en")
        url = _build_unsubscribe_url(sub.email)
        assert "/en/" in url
