"""
Tests for Reservations module views.

Tests URL routing and authentication.
"""

import pytest
from django.urls import resolve

from reservations import views


# ==============================================================================
# URL ROUTING TESTS
# ==============================================================================

@pytest.mark.django_db
class TestURLRouting:
    """Tests for URL routing and resolution."""

    def test_index_url(self):
        resolver = resolve('/modules/reservations/')
        assert resolver.func == views.index

    def test_today_url(self):
        resolver = resolve('/modules/reservations/today/')
        assert resolver.func == views.today

    def test_calendar_url(self):
        resolver = resolve('/modules/reservations/calendar/')
        assert resolver.func == views.calendar

    def test_list_url(self):
        resolver = resolve('/modules/reservations/list/')
        assert resolver.func == views.reservation_list

    def test_create_url(self):
        resolver = resolve('/modules/reservations/new/')
        assert resolver.func == views.reservation_create

    def test_waitlist_url(self):
        resolver = resolve('/modules/reservations/waitlist/')
        assert resolver.func == views.waitlist

    def test_availability_url(self):
        resolver = resolve('/modules/reservations/availability/')
        assert resolver.func == views.availability

    def test_api_for_date_url(self):
        resolver = resolve('/modules/reservations/api/for-date/')
        assert resolver.func == views.api_reservations_for_date

    def test_api_check_availability_url(self):
        resolver = resolve('/modules/reservations/api/check-availability/')
        assert resolver.func == views.api_check_availability

    def test_settings_url(self):
        resolver = resolve('/modules/reservations/settings/')
        assert resolver.func == views.settings


# ==============================================================================
# AUTHENTICATION TESTS
# ==============================================================================

@pytest.mark.django_db
class TestAuthentication:
    """Tests for view authentication requirements."""

    def test_index_requires_auth(self, client, store_config):
        response = client.get('/modules/reservations/')
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_calendar_requires_auth(self, client, store_config):
        response = client.get('/modules/reservations/calendar/')
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_settings_requires_auth(self, client, store_config):
        response = client.get('/modules/reservations/settings/')
        assert response.status_code == 302
        assert '/login/' in response.url
