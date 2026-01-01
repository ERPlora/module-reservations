"""Reservations models."""

from django.db import models
from django.utils import timezone
from datetime import timedelta


class ReservationsConfig(models.Model):
    """
    Singleton configuration for Reservations module.
    """

    # Time slot settings
    time_slot_duration = models.PositiveIntegerField(
        default=30,
        help_text="Duration of each time slot in minutes"
    )
    min_party_size = models.PositiveIntegerField(
        default=1,
        help_text="Minimum guests per reservation"
    )
    max_party_size = models.PositiveIntegerField(
        default=20,
        help_text="Maximum guests per reservation"
    )

    # Advance booking
    min_advance_hours = models.PositiveIntegerField(
        default=1,
        help_text="Minimum hours in advance to book"
    )
    max_advance_days = models.PositiveIntegerField(
        default=30,
        help_text="Maximum days in advance to book"
    )

    # Confirmation settings
    auto_confirm = models.BooleanField(
        default=False,
        help_text="Automatically confirm reservations"
    )
    require_phone = models.BooleanField(
        default=True,
        help_text="Require phone number for reservations"
    )
    require_email = models.BooleanField(
        default=False,
        help_text="Require email for reservations"
    )

    # No-show settings
    no_show_window_minutes = models.PositiveIntegerField(
        default=15,
        help_text="Minutes after reservation time to mark as no-show"
    )
    hold_table_minutes = models.PositiveIntegerField(
        default=120,
        help_text="Default reservation duration in minutes"
    )

    # Notifications
    send_confirmation_email = models.BooleanField(
        default=False,
        help_text="Send email confirmation to guests"
    )
    send_reminder_email = models.BooleanField(
        default=False,
        help_text="Send reminder email before reservation"
    )
    reminder_hours_before = models.PositiveIntegerField(
        default=24,
        help_text="Hours before to send reminder"
    )

    class Meta:
        verbose_name = "Reservations Configuration"
        verbose_name_plural = "Reservations Configuration"

    def __str__(self):
        return "Reservations Configuration"

    @classmethod
    def get_config(cls):
        """Get or create the singleton config."""
        config, _ = cls.objects.get_or_create(pk=1)
        return config


class TimeSlot(models.Model):
    """
    Defines available time slots for reservations.
    Can be used to set custom availability per day.
    """

    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_reservations = models.PositiveIntegerField(
        default=10,
        help_text="Maximum reservations for this slot"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Time Slot"
        verbose_name_plural = "Time Slots"
        ordering = ['day_of_week', 'start_time']
        unique_together = ['day_of_week', 'start_time', 'end_time']

    def __str__(self):
        day_name = dict(self.DAYS_OF_WEEK)[self.day_of_week]
        return f"{day_name} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"


class Reservation(models.Model):
    """
    Individual reservation record.
    """

    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_SEATED = 'seated'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_NO_SHOW = 'no_show'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_SEATED, 'Seated'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_NO_SHOW, 'No Show'),
    ]

    # Guest information
    guest_name = models.CharField(max_length=200)
    guest_phone = models.CharField(max_length=50, blank=True, default='')
    guest_email = models.EmailField(blank=True, default='')
    customer_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Reference to customer in customers module"
    )

    # Reservation details
    date = models.DateField(db_index=True)
    time = models.TimeField()
    party_size = models.PositiveIntegerField()
    duration_minutes = models.PositiveIntegerField(
        default=120,
        help_text="Expected duration in minutes"
    )

    # Table assignment (optional, for tables module integration)
    table_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Reference to table in tables module"
    )
    table_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text="Table number for display"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )

    # Notes
    notes = models.TextField(
        blank=True,
        default='',
        help_text="Special requests or notes"
    )
    internal_notes = models.TextField(
        blank=True,
        default='',
        help_text="Internal staff notes"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    seated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Cancellation
    cancellation_reason = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"
        ordering = ['date', 'time']
        indexes = [
            models.Index(fields=['date', 'status']),
            models.Index(fields=['guest_phone']),
        ]

    def __str__(self):
        return f"{self.guest_name} - {self.date} {self.time.strftime('%H:%M')} ({self.party_size} guests)"

    @property
    def datetime(self):
        """Return reservation datetime."""
        return timezone.make_aware(
            timezone.datetime.combine(self.date, self.time)
        )

    @property
    def end_datetime(self):
        """Return expected end datetime."""
        return self.datetime + timedelta(minutes=self.duration_minutes)

    @property
    def is_past(self):
        """Check if reservation is in the past."""
        return self.datetime < timezone.now()

    @property
    def is_today(self):
        """Check if reservation is today."""
        return self.date == timezone.now().date()

    @property
    def minutes_until(self):
        """Minutes until reservation time."""
        if self.is_past:
            return 0
        delta = self.datetime - timezone.now()
        return int(delta.total_seconds() / 60)

    @property
    def is_upcoming(self):
        """Check if reservation is within the next hour."""
        return 0 < self.minutes_until <= 60

    @property
    def status_class(self):
        """CSS class for status display."""
        return {
            self.STATUS_PENDING: 'warning',
            self.STATUS_CONFIRMED: 'primary',
            self.STATUS_SEATED: 'success',
            self.STATUS_COMPLETED: 'medium',
            self.STATUS_CANCELLED: 'danger',
            self.STATUS_NO_SHOW: 'dark',
        }.get(self.status, 'medium')

    def confirm(self):
        """Confirm the reservation."""
        if self.status == self.STATUS_PENDING:
            self.status = self.STATUS_CONFIRMED
            self.confirmed_at = timezone.now()
            self.save()
            return True
        return False

    def seat(self, table_id=None, table_number=None):
        """Mark guest as seated."""
        if self.status in [self.STATUS_PENDING, self.STATUS_CONFIRMED]:
            self.status = self.STATUS_SEATED
            self.seated_at = timezone.now()
            if table_id:
                self.table_id = table_id
            if table_number:
                self.table_number = table_number
            self.save()
            return True
        return False

    def complete(self):
        """Mark reservation as completed."""
        if self.status == self.STATUS_SEATED:
            self.status = self.STATUS_COMPLETED
            self.completed_at = timezone.now()
            self.save()
            return True
        return False

    def cancel(self, reason=''):
        """Cancel the reservation."""
        if self.status in [self.STATUS_PENDING, self.STATUS_CONFIRMED]:
            self.status = self.STATUS_CANCELLED
            self.cancelled_at = timezone.now()
            self.cancellation_reason = reason
            self.save()
            return True
        return False

    def mark_no_show(self):
        """Mark as no-show."""
        if self.status in [self.STATUS_PENDING, self.STATUS_CONFIRMED]:
            self.status = self.STATUS_NO_SHOW
            self.save()
            return True
        return False

    @classmethod
    def get_for_date(cls, date):
        """Get all active reservations for a date."""
        return cls.objects.filter(
            date=date
        ).exclude(
            status__in=[cls.STATUS_CANCELLED, cls.STATUS_NO_SHOW]
        ).order_by('time')

    @classmethod
    def get_upcoming(cls, hours=2):
        """Get upcoming reservations within specified hours."""
        now = timezone.now()
        end_time = now + timedelta(hours=hours)
        return cls.objects.filter(
            date=now.date(),
            status__in=[cls.STATUS_PENDING, cls.STATUS_CONFIRMED]
        ).order_by('time')


class BlockedDate(models.Model):
    """
    Dates when reservations are not allowed.
    Used for holidays, closures, private events, etc.
    """

    date = models.DateField(unique=True)
    reason = models.CharField(max_length=200, blank=True, default='')
    is_full_day = models.BooleanField(
        default=True,
        help_text="If false, only specific time slots are blocked"
    )
    blocked_from = models.TimeField(
        null=True,
        blank=True,
        help_text="Start time if partial day block"
    )
    blocked_until = models.TimeField(
        null=True,
        blank=True,
        help_text="End time if partial day block"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Blocked Date"
        verbose_name_plural = "Blocked Dates"
        ordering = ['date']

    def __str__(self):
        if self.is_full_day:
            return f"{self.date} - {self.reason or 'Blocked'}"
        return f"{self.date} {self.blocked_from}-{self.blocked_until} - {self.reason or 'Blocked'}"

    @classmethod
    def is_blocked(cls, date, time=None):
        """Check if a date/time is blocked."""
        blocks = cls.objects.filter(date=date)

        for block in blocks:
            if block.is_full_day:
                return True
            if time and block.blocked_from and block.blocked_until:
                if block.blocked_from <= time <= block.blocked_until:
                    return True
        return False


class WaitlistEntry(models.Model):
    """
    Waitlist for fully booked time slots.
    """

    guest_name = models.CharField(max_length=200)
    guest_phone = models.CharField(max_length=50)
    guest_email = models.EmailField(blank=True, default='')
    date = models.DateField()
    preferred_time = models.TimeField()
    party_size = models.PositiveIntegerField()
    notes = models.TextField(blank=True, default='')
    is_contacted = models.BooleanField(default=False)
    is_converted = models.BooleanField(
        default=False,
        help_text="True if converted to a reservation"
    )
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='waitlist_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Waitlist Entry"
        verbose_name_plural = "Waitlist Entries"
        ordering = ['date', 'preferred_time', 'created_at']

    def __str__(self):
        return f"{self.guest_name} - {self.date} (waitlist)"

    def convert_to_reservation(self):
        """Convert waitlist entry to a reservation."""
        if not self.is_converted:
            reservation = Reservation.objects.create(
                guest_name=self.guest_name,
                guest_phone=self.guest_phone,
                guest_email=self.guest_email,
                date=self.date,
                time=self.preferred_time,
                party_size=self.party_size,
                notes=self.notes,
                status=Reservation.STATUS_PENDING
            )
            self.is_converted = True
            self.reservation = reservation
            self.save()
            return reservation
        return None
