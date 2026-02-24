"""Tests for customers app — models."""

import pytest

from apps.customers.models import Customer


class TestCustomerModel:
    def test_str(self, customer):
        assert "John" in str(customer)
        assert "customer@test.com" in str(customer)

    def test_full_name(self, customer):
        assert customer.full_name == "John Doe"

    def test_full_name_first_only(self, db):
        c = Customer.objects.create(
            email="first@test.com", first_name="Alice", last_name=""
        )
        assert c.full_name == "Alice"

    def test_tag_list(self, customer):
        assert customer.tag_list == ["japan-interest", "repeat-customer"]

    def test_tag_list_empty(self, db):
        c = Customer.objects.create(email="notags@test.com", first_name="No")
        assert c.tag_list == []

    def test_tag_list_with_whitespace(self, db):
        c = Customer.objects.create(
            email="ws@test.com", first_name="WS", tags=" tag1 , tag2 , "
        )
        assert c.tag_list == ["tag1", "tag2"]

    def test_defaults(self, db):
        c = Customer.objects.create(email="def@test.com", first_name="Default")
        assert c.marketing_opt_in is False
        assert c.total_inquiries == 0
        assert c.total_bookings == 0

    def test_unique_email(self, customer):
        with pytest.raises(Exception):
            Customer.objects.create(email=customer.email, first_name="Dup")
