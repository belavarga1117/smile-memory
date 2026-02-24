"""Tests for accounts app — custom user model."""

import pytest

from apps.accounts.models import User


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(
            username="testuser", email="test@test.com", password="pass123"
        )
        assert user.username == "testuser"
        assert user.check_password("pass123")
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            username="superadmin", email="super@test.com", password="pass123"
        )
        assert user.is_staff
        assert user.is_superuser

    def test_default_language(self):
        user = User.objects.create_user(username="langtest", password="pass123")
        assert user.preferred_language == "th"

    def test_phone_field(self):
        user = User.objects.create_user(
            username="phonetest", password="pass123", phone="+66812345678"
        )
        assert user.phone == "+66812345678"
