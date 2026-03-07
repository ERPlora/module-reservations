"""
Tests for Reservations module models.
"""

import pytest
from datetime import date, time, timedelta
from django.utils import timezone
from freezegun import freeze_time

from reservations.models import (
    ReservationSettings,
    TimeSlot,
    Reservation,
    BlockedDate,
    WaitlistEntry,
)


# ==============================================================================
# RESERVATION SETTINGS TESTS
# ==============================================================================

@pytest.mark.django_db
class TestReservationSettings:
    """Tests for ReservationSettings model."""

    def test_create_settings(self, reservation_settings):
        """Test settings creation with defaults."""
        assert reservation_settings is not None
        assert reservation_settings.time_slot_duration == 30
        assert reservation_settings.min_party_size == 1
        assert reservation_settings.max_party_size == 20
        assert reservation_settings.min_advance_hours == 1
        assert reservation_settings.max_advance_days == 30
        assert reservation_settings.auto_confirm is False
        assert reservation_settings.require_phone is True
        assert reservation_settings.require_email is False
        assert reservation_settings.no_show_window_minutes == 15
        assert reservation_settings.default_duration_minutes == 120

    def test_str(self, reservation_settings):
        """Test string representation."""
        assert str(reservation_settings) == f'Reservation Settings (hub {reservation_settings.hub_id})'


# ==============================================================================
# TIME SLOT TESTS
# ==============================================================================

@pytest.mark.django_db
class TestTimeSlot:
    """Tests for TimeSlot model."""

    def test_creation(self, time_slot):
        """Test time slot creation."""
        assert time_slot.day_of_week == 0
        assert time_slot.start_time == time(18, 0)
        assert time_slot.end_time == time(22, 0)
        assert time_slot.max_reservations == 10
        assert time_slot.is_active is True

    def test_str(self, time_slot):
        """Test time slot string representation."""
        assert str(time_slot) == 'Monday 18:00-22:00'

    def test_ordering(self, db):
        """Test time slots are ordered by day and time."""
        slot1 = TimeSlot.objects.create(
            day_of_week=1, start_time=time(12, 0), end_time=time(14, 0),
        )
        slot2 = TimeSlot.objects.create(
            day_of_week=0, start_time=time(18, 0), end_time=time(22, 0),
        )
        slot3 = TimeSlot.objects.create(
            day_of_week=0, start_time=time(12, 0), end_time=time(14, 0),
        )
        slots = list(TimeSlot.objects.all())
        assert slots[0] == slot3  # Monday 12:00
        assert slots[1] == slot2  # Monday 18:00
        assert slots[2] == slot1  # Tuesday 12:00

    def test_unique_constraint(self, time_slot):
        """Test unique constraint on hub_id/day/start/end."""
        with pytest.raises(Exception):
            TimeSlot.objects.create(
                hub_id=time_slot.hub_id,
                day_of_week=0,
                start_time=time(18, 0),
                end_time=time(22, 0),
            )


# ==============================================================================
# RESERVATION TESTS
# ==============================================================================

@pytest.mark.django_db
class TestReservation:
    """Tests for Reservation model."""

    def test_creation(self, reservation):
        """Test reservation creation."""
        assert reservation.guest_name == 'John Doe'
        assert reservation.guest_phone == '+1234567890'
        assert reservation.party_size == 4
        assert reservation.status == 'pending'

    def test_str(self, reservation):
        s = str(reservation)
        assert 'John Doe' in s
        assert '19:00' in s
        assert '4 guests' in s

    def test_datetime_property(self, reservation):
        """Test datetime property."""
        dt = reservation.datetime
        assert dt.date() == reservation.date
        assert dt.time() == reservation.time

    def test_end_datetime(self, reservation):
        """Test end_datetime property."""
        end = reservation.end_datetime
        expected = reservation.datetime + timedelta(minutes=reservation.duration_minutes)
        assert end == expected

    def test_is_past_future(self, reservation):
        """Test is_past for future reservation."""
        assert reservation.is_past is False

    @freeze_time("2026-01-15 20:00:00")
    def test_is_past_when_past(self, db):
        """Test is_past for past reservation."""
        r = Reservation.objects.create(
            guest_name='Past Guest',
            date=date(2026, 1, 14),
            time=time(19, 0),
            party_size=2,
        )
        assert r.is_past is True

    def test_is_today(self, db):
        """Test is_today property."""
        today = timezone.now().date()
        r = Reservation.objects.create(
            guest_name='Today Guest',
            date=today,
            time=time(23, 0),
            party_size=2,
        )
        assert r.is_today is True

    def test_status_class(self, reservation):
        """Test status_class property."""
        assert reservation.status_class == 'warning'  # pending
        reservation.status = 'confirmed'
        assert reservation.status_class == 'primary'
        reservation.status = 'seated'
        assert reservation.status_class == 'success'
        reservation.status = 'cancelled'
        assert reservation.status_class == 'danger'

    def test_can_be_properties(self, reservation, confirmed_reservation, seated_reservation):
        """Test can_be_* properties."""
        assert reservation.can_be_confirmed is True
        assert reservation.can_be_seated is True
        assert reservation.can_be_cancelled is True

        assert confirmed_reservation.can_be_confirmed is False
        assert confirmed_reservation.can_be_seated is True
        assert confirmed_reservation.can_be_cancelled is True

        assert seated_reservation.can_be_confirmed is False
        assert seated_reservation.can_be_seated is False
        assert seated_reservation.can_be_completed is True
        assert seated_reservation.can_be_cancelled is False

    # ── actions ──────────────────────────────────────────────────────────

    def test_confirm(self, reservation):
        """Test confirming a pending reservation."""
        assert reservation.confirm() is True
        assert reservation.status == 'confirmed'
        assert reservation.confirmed_at is not None

    def test_confirm_non_pending_fails(self, confirmed_reservation):
        """Test confirming already confirmed reservation fails."""
        assert confirmed_reservation.confirm() is False

    def test_seat(self, confirmed_reservation):
        """Test seating a confirmed reservation."""
        assert confirmed_reservation.seat() is True
        assert confirmed_reservation.status == 'seated'
        assert confirmed_reservation.seated_at is not None

    def test_seat_pending(self, reservation):
        """Test seating a pending reservation (walk-in)."""
        assert reservation.seat() is True
        assert reservation.status == 'seated'

    def test_complete(self, seated_reservation):
        """Test completing a seated reservation."""
        assert seated_reservation.complete() is True
        assert seated_reservation.status == 'completed'
        assert seated_reservation.completed_at is not None

    def test_complete_non_seated_fails(self, confirmed_reservation):
        """Test completing non-seated reservation fails."""
        assert confirmed_reservation.complete() is False

    def test_cancel_pending(self, reservation):
        """Test cancelling a pending reservation."""
        assert reservation.cancel(reason='Changed plans') is True
        assert reservation.status == 'cancelled'
        assert reservation.cancelled_at is not None
        assert reservation.cancellation_reason == 'Changed plans'

    def test_cancel_confirmed(self, confirmed_reservation):
        """Test cancelling a confirmed reservation."""
        assert confirmed_reservation.cancel() is True
        assert confirmed_reservation.status == 'cancelled'

    def test_cancel_seated_fails(self, seated_reservation):
        """Test cancelling seated reservation fails."""
        assert seated_reservation.cancel() is False

    def test_mark_no_show(self, confirmed_reservation):
        """Test marking as no-show."""
        assert confirmed_reservation.mark_no_show() is True
        assert confirmed_reservation.status == 'no_show'

    # ── queries ──────────────────────────────────────────────────────────

    def test_get_for_date(self, db):
        """Test get_for_date class method."""
        today = timezone.now().date()
        Reservation.objects.create(
            guest_name='Guest 1', date=today, time=time(18, 0),
            party_size=2, status='pending',
        )
        Reservation.objects.create(
            guest_name='Guest 2', date=today, time=time(19, 0),
            party_size=2, status='confirmed',
        )
        Reservation.objects.create(
            guest_name='Cancelled', date=today, time=time(20, 0),
            party_size=2, status='cancelled',
        )
        reservations = Reservation.get_for_date(None, today)
        assert reservations.count() == 2  # Excludes cancelled


# ==============================================================================
# BLOCKED DATE TESTS
# ==============================================================================

@pytest.mark.django_db
class TestBlockedDate:
    """Tests for BlockedDate model."""

    def test_creation(self, blocked_date):
        """Test blocked date creation."""
        assert blocked_date.reason == 'Holiday'
        assert blocked_date.is_full_day is True

    def test_str_full_day(self, blocked_date):
        """Test string representation for full day block."""
        assert 'Holiday' in str(blocked_date)

    def test_str_partial_day(self, db):
        """Test string representation for partial day block."""
        block = BlockedDate.objects.create(
            date=date(2026, 12, 25),
            reason='Private event',
            is_full_day=False,
            blocked_from=time(18, 0),
            blocked_until=time(22, 0),
        )
        s = str(block)
        assert '18:00' in s
        assert '22:00' in s

    def test_is_blocked_full_day(self, blocked_date):
        """Test is_blocked for full day."""
        assert BlockedDate.is_blocked(None, blocked_date.date) is True
        assert BlockedDate.is_blocked(None, blocked_date.date, time(19, 0)) is True

    def test_is_blocked_partial_day(self, db):
        """Test is_blocked for partial day."""
        block_date = date(2026, 12, 31)
        BlockedDate.objects.create(
            date=block_date,
            reason='NYE Event',
            is_full_day=False,
            blocked_from=time(20, 0),
            blocked_until=time(23, 59),
        )
        assert BlockedDate.is_blocked(None, block_date, time(21, 0)) is True
        assert BlockedDate.is_blocked(None, block_date, time(18, 0)) is False

    def test_is_blocked_no_block(self, db):
        """Test is_blocked returns False when no block."""
        assert BlockedDate.is_blocked(None, date(2026, 6, 15)) is False


# ==============================================================================
# WAITLIST ENTRY TESTS
# ==============================================================================

@pytest.mark.django_db
class TestWaitlistEntry:
    """Tests for WaitlistEntry model."""

    def test_creation(self, waitlist_entry):
        """Test waitlist entry creation."""
        assert waitlist_entry.guest_name == 'Wait List Guest'
        assert waitlist_entry.party_size == 6
        assert waitlist_entry.is_converted is False
        assert waitlist_entry.is_contacted is False

    def test_str(self, waitlist_entry):
        """Test string representation."""
        assert 'Wait List Guest' in str(waitlist_entry)
        assert 'waitlist' in str(waitlist_entry)

    def test_convert_to_reservation(self, waitlist_entry):
        """Test converting waitlist entry to reservation."""
        reservation = waitlist_entry.convert_to_reservation()
        assert reservation is not None
        assert reservation.guest_name == waitlist_entry.guest_name
        assert reservation.guest_phone == waitlist_entry.guest_phone
        assert reservation.date == waitlist_entry.date
        assert reservation.time == waitlist_entry.preferred_time
        assert reservation.party_size == waitlist_entry.party_size
        assert reservation.status == 'pending'

        waitlist_entry.refresh_from_db()
        assert waitlist_entry.is_converted is True
        assert waitlist_entry.reservation == reservation

    def test_convert_already_converted_fails(self, waitlist_entry):
        """Test converting already converted entry returns None."""
        waitlist_entry.convert_to_reservation()
        result = waitlist_entry.convert_to_reservation()
        assert result is None

    def test_convert_with_auto_confirm(self, waitlist_entry, reservation_settings):
        """Test converting with auto_confirm enabled."""
        reservation_settings.auto_confirm = True
        reservation_settings.save()
        reservation = waitlist_entry.convert_to_reservation(settings=reservation_settings)
        assert reservation.status == 'confirmed'
