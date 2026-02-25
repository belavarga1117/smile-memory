"""Tests for Customer model operations — opt-in, tag filtering, properties."""

import pytest
from django.utils import timezone

from .factories import CustomerFactory


@pytest.mark.django_db
class TestCustomerModel:
    """Tests for Customer model properties and constraints."""

    def test_full_name_with_both_names(self):
        c = CustomerFactory(first_name="Somchai", last_name="Jaidee")
        assert c.full_name == "Somchai Jaidee"

    def test_full_name_only_first(self):
        c = CustomerFactory(first_name="Somchai", last_name="")
        assert c.full_name == "Somchai"

    def test_tag_list_single_tag(self):
        c = CustomerFactory(tags="japan-interest")
        assert c.tag_list == ["japan-interest"]

    def test_tag_list_multiple_tags(self):
        c = CustomerFactory(tags="japan-interest, repeat-customer, vip")
        assert "japan-interest" in c.tag_list
        assert "repeat-customer" in c.tag_list
        assert "vip" in c.tag_list
        assert len(c.tag_list) == 3

    def test_tag_list_empty(self):
        c = CustomerFactory(tags="")
        assert c.tag_list == []

    def test_str_representation(self):
        c = CustomerFactory(first_name="John", last_name="Doe", email="john@test.com")
        assert "john@test.com" in str(c)

    def test_email_unique_constraint(self):
        from django.db import IntegrityError
        from apps.customers.models import Customer

        Customer.objects.create(email="unique@test.com", first_name="Test")
        with pytest.raises(IntegrityError):
            Customer.objects.create(email="unique@test.com", first_name="Test2")

    def test_marketing_opt_in_default_false(self):
        from apps.customers.models import Customer

        c = Customer.objects.create(email="nooptin@test.com", first_name="Test")
        assert c.marketing_opt_in is False

    def test_opted_in_at_timestamp(self):
        c = CustomerFactory(marketing_opt_in=True)
        c.opted_in_at = timezone.now()
        c.save()
        c.refresh_from_db()
        assert c.opted_in_at is not None


@pytest.mark.django_db
class TestCustomerFiltering:
    """Tests for Customer queryset filtering by opt-in and tags."""

    def test_filter_opted_in_customers(self):
        from apps.customers.models import Customer

        CustomerFactory(marketing_opt_in=True)
        CustomerFactory(marketing_opt_in=True)
        CustomerFactory(marketing_opt_in=False)

        opted_in = Customer.objects.filter(marketing_opt_in=True)
        assert opted_in.count() == 2

    def test_filter_by_tag_icontains(self):
        from apps.customers.models import Customer

        CustomerFactory(marketing_opt_in=True, tags="japan-interest")
        CustomerFactory(marketing_opt_in=True, tags="europe-interest")
        CustomerFactory(marketing_opt_in=True, tags="")

        japan = Customer.objects.filter(tags__icontains="japan")
        assert japan.count() == 1

    def test_campaign_get_recipients_all_opted_in(self):
        """Campaign.get_recipients() returns all opted-in customers."""

        CustomerFactory(marketing_opt_in=True)
        CustomerFactory(marketing_opt_in=True)
        CustomerFactory(marketing_opt_in=False)

        from tests.factories import CampaignFactory

        campaign = CampaignFactory(send_to_all_opted_in=True)
        qs = campaign.get_recipients()
        assert qs.count() == 2

    def test_campaign_get_recipients_tag_filtered(self):
        """Campaign.get_recipients() respects customer_tags filter."""

        CustomerFactory(marketing_opt_in=True, tags="japan-interest")
        CustomerFactory(marketing_opt_in=True, tags="europe-interest")

        from tests.factories import CampaignFactory

        campaign = CampaignFactory(
            send_to_all_opted_in=False, customer_tags="japan-interest"
        )
        qs = campaign.get_recipients()
        assert qs.count() == 1
        assert qs.first().tags == "japan-interest"

    def test_customer_total_inquiries_default_zero(self):
        c = CustomerFactory()
        assert c.total_inquiries == 0
        assert c.total_bookings == 0


@pytest.mark.django_db
class TestCustomerAdminView:
    """Test Customer admin list/detail pages render without errors."""

    def test_customer_admin_list_accessible(self, admin_client):
        CustomerFactory()
        resp = admin_client.get("/admin/customers/customer/")
        assert resp.status_code == 200

    def test_customer_admin_detail_accessible(self, admin_client):
        c = CustomerFactory()
        resp = admin_client.get(f"/admin/customers/customer/{c.pk}/change/")
        assert resp.status_code == 200

    def test_customer_admin_search_works(self, admin_client):
        CustomerFactory(email="search_me@test.com")
        resp = admin_client.get("/admin/customers/customer/?q=search_me")
        assert resp.status_code == 200
        assert b"search_me" in resp.content
