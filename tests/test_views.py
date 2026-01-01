"""
Tests for Reservations module views.

Tests URL routing, authentication, and API endpoints.
"""

import pytest
import json
from datetime import date, time, timedelta
from django.urls import resolve
from django.utils import timezone

from reservations import views
from reservations.models import (
    Reservation,
    ReservationsConfig,
    BlockedDate,
    WaitlistEntry
)


# ==============================================================================
# URL ROUTING TESTS
# ==============================================================================

@pytest.mark.django_db
class TestURLRouting:
    """Tests for URL routing and resolution."""

    def test_index_url_resolves(self):
        """Test index URL resolves."""
        resolver = resolve('/modules/reservations/')
        assert resolver.func == views.index

    def test_calendar_url_resolves(self):
        """Test calendar URL resolves."""
        resolver = resolve('/modules/reservations/calendar/')
        assert resolver.func == views.calendar

    def test_list_url_resolves(self):
        """Test list URL resolves."""
        resolver = resolve('/modules/reservations/list/')
        assert resolver.func == views.reservation_list

    def test_create_url_resolves(self):
        """Test create URL resolves."""
        resolver = resolve('/modules/reservations/new/')
        assert resolver.func == views.reservation_create

    def test_detail_url_resolves(self):
        """Test detail URL resolves."""
        resolver = resolve('/modules/reservations/1/')
        assert resolver.func == views.reservation_detail

    def test_edit_url_resolves(self):
        """Test edit URL resolves."""
        resolver = resolve('/modules/reservations/1/edit/')
        assert resolver.func == views.reservation_edit

    def test_waitlist_url_resolves(self):
        """Test waitlist URL resolves."""
        resolver = resolve('/modules/reservations/waitlist/')
        assert resolver.func == views.waitlist

    def test_blocked_dates_url_resolves(self):
        """Test blocked dates URL resolves."""
        resolver = resolve('/modules/reservations/blocked/')
        assert resolver.func == views.blocked_dates

    def test_time_slots_url_resolves(self):
        """Test time slots URL resolves."""
        resolver = resolve('/modules/reservations/slots/')
        assert resolver.func == views.time_slots

    def test_api_create_url_resolves(self):
        """Test API create URL resolves."""
        resolver = resolve('/modules/reservations/api/create/')
        assert resolver.func == views.api_create_reservation

    def test_api_confirm_url_resolves(self):
        """Test API confirm URL resolves."""
        resolver = resolve('/modules/reservations/api/confirm/')
        assert resolver.func == views.api_confirm_reservation

    def test_api_seat_url_resolves(self):
        """Test API seat URL resolves."""
        resolver = resolve('/modules/reservations/api/seat/')
        assert resolver.func == views.api_seat_reservation

    def test_api_complete_url_resolves(self):
        """Test API complete URL resolves."""
        resolver = resolve('/modules/reservations/api/complete/')
        assert resolver.func == views.api_complete_reservation

    def test_api_cancel_url_resolves(self):
        """Test API cancel URL resolves."""
        resolver = resolve('/modules/reservations/api/cancel/')
        assert resolver.func == views.api_cancel_reservation

    def test_api_no_show_url_resolves(self):
        """Test API no-show URL resolves."""
        resolver = resolve('/modules/reservations/api/no-show/')
        assert resolver.func == views.api_no_show_reservation

    def test_api_for_date_url_resolves(self):
        """Test API for-date URL resolves."""
        resolver = resolve('/modules/reservations/api/for-date/')
        assert resolver.func == views.api_reservations_for_date

    def test_api_check_availability_url_resolves(self):
        """Test API check-availability URL resolves."""
        resolver = resolve('/modules/reservations/api/check-availability/')
        assert resolver.func == views.api_check_availability

    def test_settings_url_resolves(self):
        """Test settings URL resolves."""
        resolver = resolve('/modules/reservations/settings/')
        assert resolver.func == views.reservations_settings


# ==============================================================================
# AUTHENTICATION TESTS
# ==============================================================================

@pytest.mark.django_db
class TestAuthentication:
    """Tests for view authentication requirements."""

    def test_index_requires_auth(self, client, store_config):
        """Test index requires authentication."""
        response = client.get('/modules/reservations/')
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_calendar_requires_auth(self, client, store_config):
        """Test calendar requires authentication."""
        response = client.get('/modules/reservations/calendar/')
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_api_create_requires_auth(self, client, store_config):
        """Test API create requires authentication."""
        response = client.post('/modules/reservations/api/create/')
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_settings_requires_auth(self, client, store_config):
        """Test settings requires authentication."""
        response = client.get('/modules/reservations/settings/')
        assert response.status_code == 302
        assert '/login/' in response.url


# ==============================================================================
# RESERVATION API TESTS
# ==============================================================================

@pytest.mark.django_db
class TestReservationAPI:
    """Tests for reservation API endpoints."""

    def test_api_create_reservation(self, auth_client, reservations_config):
        """Test creating a reservation."""
        tomorrow = (timezone.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = auth_client.post(
            '/modules/reservations/api/create/',
            json.dumps({
                'guest_name': 'Test Guest',
                'guest_phone': '+1234567890',
                'date': tomorrow,
                'time': '19:00',
                'party_size': 4
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert 'reservation_id' in data

    def test_api_create_without_name_fails(self, auth_client, reservations_config):
        """Test creating reservation without name fails."""
        tomorrow = (timezone.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = auth_client.post(
            '/modules/reservations/api/create/',
            json.dumps({
                'guest_phone': '+1234567890',
                'date': tomorrow,
                'time': '19:00',
                'party_size': 4
            }),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_api_create_without_phone_fails_when_required(self, auth_client, reservations_config):
        """Test creating reservation without phone fails when required."""
        reservations_config.require_phone = True
        reservations_config.save()

        tomorrow = (timezone.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = auth_client.post(
            '/modules/reservations/api/create/',
            json.dumps({
                'guest_name': 'Test Guest',
                'date': tomorrow,
                'time': '19:00',
                'party_size': 4
            }),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_api_create_auto_confirm(self, auth_client, reservations_config):
        """Test auto-confirm creates confirmed reservation."""
        reservations_config.auto_confirm = True
        reservations_config.require_phone = False
        reservations_config.save()

        tomorrow = (timezone.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = auth_client.post(
            '/modules/reservations/api/create/',
            json.dumps({
                'guest_name': 'Auto Guest',
                'date': tomorrow,
                'time': '19:00',
                'party_size': 2
            }),
            content_type='application/json'
        )
        data = json.loads(response.content)
        assert data['status'] == 'confirmed'

    def test_api_confirm_reservation(self, auth_client, reservation):
        """Test confirming a reservation."""
        response = auth_client.post(
            '/modules/reservations/api/confirm/',
            {'reservation_id': reservation.id}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['status'] == 'confirmed'

    def test_api_confirm_non_pending_fails(self, auth_client, confirmed_reservation):
        """Test confirming already confirmed fails."""
        response = auth_client.post(
            '/modules/reservations/api/confirm/',
            {'reservation_id': confirmed_reservation.id}
        )
        assert response.status_code == 400

    def test_api_seat_reservation(self, auth_client, confirmed_reservation):
        """Test seating a reservation."""
        response = auth_client.post(
            '/modules/reservations/api/seat/',
            {
                'reservation_id': confirmed_reservation.id,
                'table_id': 5,
                'table_number': 'T5'
            }
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['status'] == 'seated'

    def test_api_complete_reservation(self, auth_client, seated_reservation):
        """Test completing a reservation."""
        response = auth_client.post(
            '/modules/reservations/api/complete/',
            {'reservation_id': seated_reservation.id}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['status'] == 'completed'

    def test_api_cancel_reservation(self, auth_client, reservation):
        """Test cancelling a reservation."""
        response = auth_client.post(
            '/modules/reservations/api/cancel/',
            {
                'reservation_id': reservation.id,
                'reason': 'Changed plans'
            }
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['status'] == 'cancelled'

    def test_api_no_show_reservation(self, auth_client, confirmed_reservation):
        """Test marking as no-show."""
        response = auth_client.post(
            '/modules/reservations/api/no-show/',
            {'reservation_id': confirmed_reservation.id}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['status'] == 'no_show'


# ==============================================================================
# QUERY API TESTS
# ==============================================================================

@pytest.mark.django_db
class TestQueryAPI:
    """Tests for query API endpoints."""

    def test_api_reservations_for_date(self, auth_client, reservation, confirmed_reservation):
        """Test getting reservations for a date."""
        date_str = reservation.date.strftime('%Y-%m-%d')
        response = auth_client.get(f'/modules/reservations/api/for-date/?date={date_str}')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert len(data['reservations']) >= 1

    def test_api_reservations_for_date_missing_date(self, auth_client, store_config):
        """Test for-date without date parameter fails."""
        response = auth_client.get('/modules/reservations/api/for-date/')
        assert response.status_code == 400

    def test_api_check_availability(self, auth_client, store_config):
        """Test checking availability."""
        tomorrow = (timezone.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = auth_client.get(
            f'/modules/reservations/api/check-availability/?date={tomorrow}&time=19:00&party_size=4'
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert 'available' in data

    def test_api_check_availability_blocked_date(self, auth_client, blocked_date):
        """Test availability returns blocked for blocked date."""
        date_str = blocked_date.date.strftime('%Y-%m-%d')
        response = auth_client.get(
            f'/modules/reservations/api/check-availability/?date={date_str}&time=19:00&party_size=4'
        )
        data = json.loads(response.content)
        assert data['available'] is False
        assert data['is_blocked'] is True


# ==============================================================================
# WAITLIST API TESTS
# ==============================================================================

@pytest.mark.django_db
class TestWaitlistAPI:
    """Tests for waitlist API endpoints."""

    def test_api_add_to_waitlist(self, auth_client, store_config):
        """Test adding to waitlist."""
        tomorrow = (timezone.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = auth_client.post(
            '/modules/reservations/api/waitlist/add/',
            json.dumps({
                'guest_name': 'Waitlist Guest',
                'guest_phone': '+1234567890',
                'date': tomorrow,
                'time': '19:00',
                'party_size': 6
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert 'entry_id' in data

    def test_api_convert_waitlist(self, auth_client, waitlist_entry):
        """Test converting waitlist entry."""
        response = auth_client.post(
            '/modules/reservations/api/waitlist/convert/',
            {'entry_id': waitlist_entry.id}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert 'reservation_id' in data


# ==============================================================================
# BLOCKED DATE API TESTS
# ==============================================================================

@pytest.mark.django_db
class TestBlockedDateAPI:
    """Tests for blocked date API endpoints."""

    def test_api_block_date(self, auth_client, store_config):
        """Test blocking a date."""
        future_date = (timezone.now().date() + timedelta(days=14)).strftime('%Y-%m-%d')
        response = auth_client.post(
            '/modules/reservations/api/block/',
            json.dumps({
                'date': future_date,
                'reason': 'Private Event',
                'is_full_day': 'true'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert 'block_id' in data

    def test_api_unblock_date(self, auth_client, blocked_date):
        """Test unblocking a date."""
        response = auth_client.post(
            '/modules/reservations/api/unblock/',
            {'block_id': blocked_date.id}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True

        assert not BlockedDate.objects.filter(id=blocked_date.id).exists()


# ==============================================================================
# SETTINGS TESTS
# ==============================================================================

@pytest.mark.django_db
class TestSettingsView:
    """Tests for settings views."""

    def test_settings_save_success(self, auth_client, store_config):
        """Test saving settings."""
        response = auth_client.post(
            '/modules/reservations/settings/save/',
            json.dumps({
                'time_slot_duration': 45,
                'max_party_size': 15,
                'auto_confirm': True,
                'require_phone': False
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True

        config = ReservationsConfig.get_config()
        assert config.time_slot_duration == 45
        assert config.max_party_size == 15
        assert config.auto_confirm is True
        assert config.require_phone is False

    def test_settings_save_invalid_json(self, auth_client, store_config):
        """Test saving settings with invalid JSON."""
        response = auth_client.post(
            '/modules/reservations/settings/save/',
            'invalid json',
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_settings_toggle(self, auth_client, store_config):
        """Test toggling a boolean setting."""
        response = auth_client.post(
            '/modules/reservations/settings/toggle/',
            {'name': 'auto_confirm', 'value': 'true'}
        )
        assert response.status_code == 204

        config = ReservationsConfig.get_config()
        assert config.auto_confirm is True

    def test_settings_input(self, auth_client, store_config):
        """Test updating a numeric setting."""
        response = auth_client.post(
            '/modules/reservations/settings/input/',
            {'name': 'max_party_size', 'value': '25'}
        )
        assert response.status_code == 204

        config = ReservationsConfig.get_config()
        assert config.max_party_size == 25

    def test_settings_reset(self, auth_client, reservations_config):
        """Test resetting settings to defaults."""
        # First change some settings
        reservations_config.max_party_size = 50
        reservations_config.auto_confirm = True
        reservations_config.save()

        # Reset
        response = auth_client.post('/modules/reservations/settings/reset/')
        assert response.status_code == 204

        # Verify reset to defaults
        reservations_config.refresh_from_db()
        assert reservations_config.max_party_size == 20
        assert reservations_config.auto_confirm is False
