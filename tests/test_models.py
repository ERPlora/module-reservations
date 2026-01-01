"""
Tests for Reservations module models.

Tests model creation, validation, and business logic.
"""

import pytest
from datetime import date, time, timedelta
from django.utils import timezone
from freezegun import freeze_time

from reservations.models import (
    ReservationsConfig,
    TimeSlot,
    Reservation,
    BlockedDate,
    WaitlistEntry
)


# ==============================================================================
# RESERVATIONS CONFIG TESTS
# ==============================================================================

@pytest.mark.django_db
class TestReservationsConfig:
    """Tests for ReservationsConfig model."""

    def test_get_config_creates_singleton(self):
        """Test get_config creates config if not exists."""
        config = ReservationsConfig.get_config()
        assert config is not None
        assert config.pk == 1

    def test_config_default_values(self, reservations_config):
        """Test config has correct defaults."""
        assert reservations_config.time_slot_duration == 30
        assert reservations_config.min_party_size == 1
        assert reservations_config.max_party_size == 20
        assert reservations_config.min_advance_hours == 1
        assert reservations_config.max_advance_days == 30
        assert reservations_config.auto_confirm is False
        assert reservations_config.require_phone is True
        assert reservations_config.require_email is False
        assert reservations_config.no_show_window_minutes == 15
        assert reservations_config.hold_table_minutes == 120

    def test_config_str(self, reservations_config):
        """Test config string representation."""
        assert str(reservations_config) == "Reservations Configuration"

    def test_config_is_singleton(self, reservations_config):
        """Test only one config can exist."""
        config2 = ReservationsConfig.get_config()
        assert config2.pk == reservations_config.pk


# ==============================================================================
# TIME SLOT TESTS
# ==============================================================================

@pytest.mark.django_db
class TestTimeSlot:
    """Tests for TimeSlot model."""

    def test_time_slot_creation(self, time_slot):
        """Test time slot creation."""
        assert time_slot.day_of_week == 0
        assert time_slot.start_time == time(18, 0)
        assert time_slot.end_time == time(22, 0)
        assert time_slot.max_reservations == 10
        assert time_slot.is_active is True

    def test_time_slot_str(self, time_slot):
        """Test time slot string representation."""
        assert str(time_slot) == "Monday 18:00-22:00"

    def test_time_slot_ordering(self, db):
        """Test time slots are ordered by day and time."""
        slot1 = TimeSlot.objects.create(
            day_of_week=1, start_time=time(12, 0), end_time=time(14, 0)
        )
        slot2 = TimeSlot.objects.create(
            day_of_week=0, start_time=time(18, 0), end_time=time(22, 0)
        )
        slot3 = TimeSlot.objects.create(
            day_of_week=0, start_time=time(12, 0), end_time=time(14, 0)
        )

        slots = list(TimeSlot.objects.all())
        assert slots[0] == slot3  # Monday 12:00
        assert slots[1] == slot2  # Monday 18:00
        assert slots[2] == slot1  # Tuesday 12:00

    def test_time_slot_unique_constraint(self, time_slot):
        """Test unique constraint on day/start/end."""
        with pytest.raises(Exception):
            TimeSlot.objects.create(
                day_of_week=0,
                start_time=time(18, 0),
                end_time=time(22, 0)
            )


# ==============================================================================
# RESERVATION TESTS
# ==============================================================================

@pytest.mark.django_db
class TestReservation:
    """Tests for Reservation model."""

    def test_reservation_creation(self, reservation):
        """Test reservation creation."""
        assert reservation.guest_name == 'John Doe'
        assert reservation.guest_phone == '+1234567890'
        assert reservation.party_size == 4
        assert reservation.status == Reservation.STATUS_PENDING

    def test_reservation_str(self, reservation):
        """Test reservation string representation."""
        expected = f"John Doe - {reservation.date} 19:00 (4 guests)"
        assert str(reservation) == expected

    def test_reservation_datetime(self, reservation):
        """Test datetime property."""
        dt = reservation.datetime
        assert dt.date() == reservation.date
        assert dt.time() == reservation.time

    def test_reservation_end_datetime(self, reservation):
        """Test end_datetime property."""
        end = reservation.end_datetime
        expected = reservation.datetime + timedelta(minutes=reservation.duration_minutes)
        assert end == expected

    def test_reservation_is_past(self, reservation):
        """Test is_past property for future reservation."""
        assert reservation.is_past is False

    @freeze_time("2024-01-15 20:00:00")
    def test_reservation_is_past_when_past(self, db):
        """Test is_past property for past reservation."""
        past_date = date(2024, 1, 14)
        reservation = Reservation.objects.create(
            guest_name='Past Guest',
            date=past_date,
            time=time(19, 0),
            party_size=2
        )
        assert reservation.is_past is True

    def test_reservation_is_today(self, db):
        """Test is_today property."""
        today = timezone.now().date()
        reservation = Reservation.objects.create(
            guest_name='Today Guest',
            date=today,
            time=time(23, 0),
            party_size=2
        )
        assert reservation.is_today is True

    def test_reservation_status_class(self, reservation):
        """Test status_class property."""
        assert reservation.status_class == 'warning'  # pending

        reservation.status = Reservation.STATUS_CONFIRMED
        assert reservation.status_class == 'primary'

        reservation.status = Reservation.STATUS_SEATED
        assert reservation.status_class == 'success'

        reservation.status = Reservation.STATUS_CANCELLED
        assert reservation.status_class == 'danger'

    def test_confirm_pending_reservation(self, reservation):
        """Test confirming a pending reservation."""
        result = reservation.confirm()
        assert result is True
        assert reservation.status == Reservation.STATUS_CONFIRMED
        assert reservation.confirmed_at is not None

    def test_confirm_non_pending_fails(self, confirmed_reservation):
        """Test confirming already confirmed reservation fails."""
        result = confirmed_reservation.confirm()
        assert result is False

    def test_seat_confirmed_reservation(self, confirmed_reservation):
        """Test seating a confirmed reservation."""
        result = confirmed_reservation.seat(table_id=5, table_number='T5')
        assert result is True
        assert confirmed_reservation.status == Reservation.STATUS_SEATED
        assert confirmed_reservation.seated_at is not None
        assert confirmed_reservation.table_id == 5
        assert confirmed_reservation.table_number == 'T5'

    def test_seat_pending_reservation(self, reservation):
        """Test seating a pending reservation (walk-in)."""
        result = reservation.seat()
        assert result is True
        assert reservation.status == Reservation.STATUS_SEATED

    def test_complete_seated_reservation(self, seated_reservation):
        """Test completing a seated reservation."""
        result = seated_reservation.complete()
        assert result is True
        assert seated_reservation.status == Reservation.STATUS_COMPLETED
        assert seated_reservation.completed_at is not None

    def test_complete_non_seated_fails(self, confirmed_reservation):
        """Test completing non-seated reservation fails."""
        result = confirmed_reservation.complete()
        assert result is False

    def test_cancel_pending_reservation(self, reservation):
        """Test cancelling a pending reservation."""
        result = reservation.cancel(reason='Changed plans')
        assert result is True
        assert reservation.status == Reservation.STATUS_CANCELLED
        assert reservation.cancelled_at is not None
        assert reservation.cancellation_reason == 'Changed plans'

    def test_cancel_confirmed_reservation(self, confirmed_reservation):
        """Test cancelling a confirmed reservation."""
        result = confirmed_reservation.cancel()
        assert result is True
        assert confirmed_reservation.status == Reservation.STATUS_CANCELLED

    def test_cancel_seated_fails(self, seated_reservation):
        """Test cancelling seated reservation fails."""
        result = seated_reservation.cancel()
        assert result is False

    def test_mark_no_show(self, confirmed_reservation):
        """Test marking as no-show."""
        result = confirmed_reservation.mark_no_show()
        assert result is True
        assert confirmed_reservation.status == Reservation.STATUS_NO_SHOW

    def test_get_for_date(self, db):
        """Test get_for_date class method."""
        today = timezone.now().date()

        # Create reservations
        Reservation.objects.create(
            guest_name='Guest 1', date=today, time=time(18, 0), party_size=2,
            status=Reservation.STATUS_PENDING
        )
        Reservation.objects.create(
            guest_name='Guest 2', date=today, time=time(19, 0), party_size=2,
            status=Reservation.STATUS_CONFIRMED
        )
        Reservation.objects.create(
            guest_name='Cancelled', date=today, time=time(20, 0), party_size=2,
            status=Reservation.STATUS_CANCELLED
        )

        reservations = Reservation.get_for_date(today)
        assert reservations.count() == 2  # Excludes cancelled


# ==============================================================================
# BLOCKED DATE TESTS
# ==============================================================================

@pytest.mark.django_db
class TestBlockedDate:
    """Tests for BlockedDate model."""

    def test_blocked_date_creation(self, blocked_date):
        """Test blocked date creation."""
        assert blocked_date.reason == 'Holiday'
        assert blocked_date.is_full_day is True

    def test_blocked_date_str_full_day(self, blocked_date):
        """Test string representation for full day block."""
        assert 'Holiday' in str(blocked_date)

    def test_blocked_date_str_partial_day(self, db):
        """Test string representation for partial day block."""
        block = BlockedDate.objects.create(
            date=date(2024, 12, 25),
            reason='Private event',
            is_full_day=False,
            blocked_from=time(18, 0),
            blocked_until=time(22, 0)
        )
        # Check that the time range is in the string representation
        block_str = str(block)
        assert '18:00' in block_str
        assert '22:00' in block_str

    def test_is_blocked_full_day(self, blocked_date):
        """Test is_blocked for full day."""
        assert BlockedDate.is_blocked(blocked_date.date) is True
        assert BlockedDate.is_blocked(blocked_date.date, time(19, 0)) is True

    def test_is_blocked_partial_day(self, db):
        """Test is_blocked for partial day."""
        block_date = date(2024, 12, 31)
        BlockedDate.objects.create(
            date=block_date,
            reason='NYE Event',
            is_full_day=False,
            blocked_from=time(20, 0),
            blocked_until=time(23, 59)
        )

        assert BlockedDate.is_blocked(block_date, time(21, 0)) is True
        assert BlockedDate.is_blocked(block_date, time(18, 0)) is False

    def test_is_blocked_no_block(self, db):
        """Test is_blocked returns False when no block."""
        assert BlockedDate.is_blocked(date(2024, 6, 15)) is False


# ==============================================================================
# WAITLIST ENTRY TESTS
# ==============================================================================

@pytest.mark.django_db
class TestWaitlistEntry:
    """Tests for WaitlistEntry model."""

    def test_waitlist_entry_creation(self, waitlist_entry):
        """Test waitlist entry creation."""
        assert waitlist_entry.guest_name == 'Wait List Guest'
        assert waitlist_entry.party_size == 6
        assert waitlist_entry.is_converted is False
        assert waitlist_entry.is_contacted is False

    def test_waitlist_entry_str(self, waitlist_entry):
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
        assert reservation.status == Reservation.STATUS_PENDING

        waitlist_entry.refresh_from_db()
        assert waitlist_entry.is_converted is True
        assert waitlist_entry.reservation == reservation

    def test_convert_already_converted_fails(self, waitlist_entry):
        """Test converting already converted entry returns None."""
        waitlist_entry.convert_to_reservation()
        result = waitlist_entry.convert_to_reservation()
        assert result is None
