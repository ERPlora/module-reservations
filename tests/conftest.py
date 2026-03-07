"""
Pytest fixtures for Reservations module tests.
"""

import pytest
from datetime import time, timedelta
from django.utils import timezone

from apps.accounts.models import LocalUser
from apps.configuration.models import StoreConfig

from reservations.models import (
    Reservation,
    ReservationSettings,
    TimeSlot,
    BlockedDate,
    WaitlistEntry,
)


@pytest.fixture
def local_user(db):
    """Create a test user."""
    from django.contrib.auth.hashers import make_password
    return LocalUser.objects.create(
        name='Test User',
        email='test@example.com',
        role='admin',
        pin_hash=make_password('1234'),
        is_active=True,
    )


@pytest.fixture
def user(local_user):
    """Alias for local_user fixture."""
    return local_user


@pytest.fixture
def store_config(db):
    """Create store config for tests."""
    config = StoreConfig.get_config()
    config.is_configured = True
    config.name = 'Test Store'
    config.save()
    return config


@pytest.fixture
def auth_client(client, local_user, store_config):
    """Return an authenticated client."""
    session = client.session
    session['local_user_id'] = str(local_user.id)
    session['user_name'] = local_user.name
    session['user_email'] = local_user.email
    session['user_role'] = local_user.role
    session['store_config_checked'] = True
    session.save()
    return client


@pytest.fixture
def reservation_settings(db):
    """Create reservation settings."""
    return ReservationSettings.objects.create()


@pytest.fixture
def reservation(db):
    """Create a basic pending reservation."""
    tomorrow = timezone.now().date() + timedelta(days=1)
    return Reservation.objects.create(
        guest_name='John Doe',
        guest_phone='+1234567890',
        guest_email='john@example.com',
        date=tomorrow,
        time=time(19, 0),
        party_size=4,
        status='pending',
    )


@pytest.fixture
def confirmed_reservation(db):
    """Create a confirmed reservation."""
    tomorrow = timezone.now().date() + timedelta(days=1)
    return Reservation.objects.create(
        guest_name='Jane Smith',
        guest_phone='+0987654321',
        guest_email='jane@example.com',
        date=tomorrow,
        time=time(20, 0),
        party_size=2,
        status='confirmed',
        confirmed_at=timezone.now(),
    )


@pytest.fixture
def seated_reservation(db):
    """Create a seated reservation."""
    today = timezone.now().date()
    return Reservation.objects.create(
        guest_name='Bob Wilson',
        guest_phone='+1111111111',
        guest_email='bob@example.com',
        date=today,
        time=time(18, 0),
        party_size=3,
        status='seated',
        seated_at=timezone.now(),
    )


@pytest.fixture
def time_slot(db):
    """Create a time slot."""
    return TimeSlot.objects.create(
        day_of_week=0,  # Monday
        start_time=time(18, 0),
        end_time=time(22, 0),
        max_reservations=10,
        is_active=True,
    )


@pytest.fixture
def blocked_date(db):
    """Create a blocked date."""
    future_date = timezone.now().date() + timedelta(days=7)
    return BlockedDate.objects.create(
        date=future_date,
        reason='Holiday',
        is_full_day=True,
    )


@pytest.fixture
def waitlist_entry(db):
    """Create a waitlist entry."""
    tomorrow = timezone.now().date() + timedelta(days=1)
    return WaitlistEntry.objects.create(
        guest_name='Wait List Guest',
        guest_phone='+5555555555',
        date=tomorrow,
        preferred_time=time(19, 30),
        party_size=6,
    )
