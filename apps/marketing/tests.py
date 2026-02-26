"""Tests for marketing app — models, views."""

import uuid

import pytest

from apps.customers.models import Customer
from apps.marketing.models import Campaign, Subscriber


# ── Model Tests ──


class TestEmailTemplateModel:
    def test_str(self, email_template):
        assert str(email_template) == "Monthly Newsletter"


class TestCampaignModel:
    def test_str(self, campaign):
        assert "January Newsletter" in str(campaign)
        assert "Draft" in str(campaign)

    def test_get_effective_subject_template(self, campaign, email_template):
        assert campaign.get_effective_subject() == email_template.subject

    def test_get_effective_subject_direct(self, db):
        c = Campaign.objects.create(
            name="Direct",
            subject="Direct Subject",
            body_html="<p>Hello</p>",
        )
        assert c.get_effective_subject() == "Direct Subject"

    def test_get_effective_body_html_template(self, campaign, email_template):
        assert campaign.get_effective_body_html() == email_template.body_html

    def test_get_recipients_all_opted_in(self, campaign, customer):
        recipients = campaign.get_recipients()
        assert customer in recipients

    def test_get_recipients_not_opted_in(self, campaign, db):
        Customer.objects.create(
            email="nooptin@test.com", first_name="No", marketing_opt_in=False
        )
        recipients = campaign.get_recipients()
        assert not recipients.filter(email="nooptin@test.com").exists()

    def test_get_recipients_tag_filter(self, db, customer):
        c = Campaign.objects.create(
            name="Tagged",
            subject="Tagged Campaign",
            body_html="<p>Hi</p>",
            send_to_all_opted_in=False,
            customer_tags="japan-interest",
        )
        recipients = c.get_recipients()
        assert customer in recipients

    def test_get_recipients_tag_no_match(self, db, customer):
        c = Campaign.objects.create(
            name="No Match",
            subject="No Match",
            body_html="<p>Hi</p>",
            send_to_all_opted_in=False,
            customer_tags="europe-interest",
        )
        recipients = c.get_recipients()
        assert customer not in recipients


class TestSubscriberModel:
    def test_str_active(self, subscriber):
        assert "active" in str(subscriber)

    def test_str_inactive(self, subscriber):
        subscriber.is_active = False
        subscriber.save()
        assert "unsubscribed" in str(subscriber)

    def test_unsubscribe_token(self, subscriber):
        assert subscriber.unsubscribe_token is not None
        assert isinstance(subscriber.unsubscribe_token, uuid.UUID)


# ── View Tests ──


@pytest.mark.django_db
class TestNewsletterSubscribeView:
    def test_subscribe_new_email(self, client):
        resp = client.post(
            "/th/newsletter/subscribe/",
            {"email": "new@test.com", "source": "footer"},
            HTTP_REFERER="/th/",
        )
        assert resp.status_code == 302
        assert Subscriber.objects.filter(email="new@test.com").exists()

    def test_subscribe_existing_reactivates(self, client, subscriber):
        subscriber.is_active = False
        subscriber.save()
        resp = client.post(
            "/th/newsletter/subscribe/",
            {"email": subscriber.email},
            HTTP_REFERER="/th/",
        )
        assert resp.status_code == 302
        subscriber.refresh_from_db()
        assert subscriber.is_active is True

    def test_subscribe_empty_email(self, client):
        resp = client.post(
            "/th/newsletter/subscribe/",
            {"email": ""},
            HTTP_REFERER="/th/",
        )
        assert resp.status_code == 302  # Redirects back with error

    def test_subscribe_does_not_link_customer_before_confirm(self, client, customer):
        # Double opt-in: customer linking only happens after email confirmation
        resp = client.post(
            "/th/newsletter/subscribe/",
            {"email": customer.email},
            HTTP_REFERER="/th/",
        )
        assert resp.status_code == 302
        sub = Subscriber.objects.get(email=customer.email)
        assert sub.customer is None
        assert sub.is_confirmed is False


@pytest.mark.django_db
class TestNewsletterConfirmView:
    def test_confirm_sets_confirmed(self, client, subscriber):
        subscriber.is_confirmed = False
        subscriber.save()
        url = f"/th/newsletter/confirm/{subscriber.confirmation_token}/"
        resp = client.get(url)
        assert resp.status_code == 200
        subscriber.refresh_from_db()
        assert subscriber.is_confirmed is True
        assert subscriber.confirmed_at is not None

    def test_confirm_links_customer(self, client, customer):
        sub = Subscriber.objects.create(
            email=customer.email,
            is_active=True,
            is_confirmed=False,
            source="footer",
        )
        url = f"/th/newsletter/confirm/{sub.confirmation_token}/"
        client.get(url)
        sub.refresh_from_db()
        assert sub.customer == customer
        customer.refresh_from_db()
        assert customer.marketing_opt_in is True

    def test_confirm_invalid_token_404(self, client):
        fake_token = uuid.uuid4()
        url = f"/th/newsletter/confirm/{fake_token}/"
        resp = client.get(url)
        assert resp.status_code == 404

    def test_confirm_idempotent(self, client, subscriber):
        # Clicking confirm link twice should be safe
        subscriber.is_confirmed = False
        subscriber.save()
        url = f"/th/newsletter/confirm/{subscriber.confirmation_token}/"
        client.get(url)
        client.get(url)
        subscriber.refresh_from_db()
        assert subscriber.is_confirmed is True


@pytest.mark.django_db
class TestNewsletterUnsubscribeView:
    def test_unsubscribe_get(self, client, subscriber):
        url = f"/th/newsletter/unsubscribe/{subscriber.unsubscribe_token}/"
        resp = client.get(url)
        assert resp.status_code == 200

    def test_unsubscribe_post(self, client, subscriber):
        url = f"/th/newsletter/unsubscribe/{subscriber.unsubscribe_token}/"
        resp = client.post(url)
        assert resp.status_code == 200
        subscriber.refresh_from_db()
        assert subscriber.is_active is False

    def test_unsubscribe_updates_customer(self, client, subscriber, customer):
        url = f"/th/newsletter/unsubscribe/{subscriber.unsubscribe_token}/"
        client.post(url)
        customer.refresh_from_db()
        assert customer.marketing_opt_in is False

    def test_invalid_token_404(self, client):
        fake_token = uuid.uuid4()
        url = f"/th/newsletter/unsubscribe/{fake_token}/"
        resp = client.get(url)
        assert resp.status_code == 404
