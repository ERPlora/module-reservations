"""Reservations models.

Models:
- ReservationSettings — per-hub configuration
- TimeSlot — available time windows per day of week
- BlockedDate — dates/times when reservations aren't allowed
- Reservation — individual reservation record
- WaitlistEntry — waitlist for fully booked slots
"""

from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import HubBaseModel


# ==============================================================================
# SETTINGS
# ==============================================================================

class ReservationSettings(HubBaseModel):
    """Per-hub reservation settings."""

    # Time slot settings
    time_slot_duration = models.PositiveIntegerField(default=30, help_text=_('Duration of each time slot in minutes'))
    min_party_size = models.PositiveIntegerField(default=1)
    max_party_size = models.PositiveIntegerField(default=20)

    # Advance booking
    min_advance_hours = models.PositiveIntegerField(default=1, help_text=_('Minimum hours in advance to book'))
    max_advance_days = models.PositiveIntegerField(default=30, help_text=_('Maximum days in advance to book'))

    # Confirmation
    auto_confirm = models.BooleanField(default=False, help_text=_('Automatically confirm reservations'))
    require_phone = models.BooleanField(default=True)
    require_email = models.BooleanField(default=False)

    # No-show / duration
    no_show_window_minutes = models.PositiveIntegerField(default=15, help_text=_('Minutes after time to mark as no-show'))
    default_duration_minutes = models.PositiveIntegerField(default=120, help_text=_('Default reservation duration'))

    # Notifications
    send_confirmation_email = models.BooleanField(default=False)
    send_reminder_email = models.BooleanField(default=False)
    reminder_hours_before = models.PositiveIntegerField(default=24)

    class Meta(HubBaseModel.Meta):
        db_table = 'reservations_settings'
        verbose_name = _('Reservation Settings')
        verbose_name_plural = _('Reservation Settings')
        constraints = [
            models.UniqueConstraint(fields=['hub_id'], name='unique_reservation_settings_per_hub'),
        ]

    def __str__(self):
        return f'Reservation Settings (hub {self.hub_id})'

    @classmethod
    def get_settings(cls, hub_id):
        try:
            return cls.all_objects.get(hub_id=hub_id)
        except cls.DoesNotExist:
            from django.db import IntegrityError
            try:
                return cls.all_objects.create(hub_id=hub_id)
            except IntegrityError:
                return cls.all_objects.get(hub_id=hub_id)


# ==============================================================================
# TIME SLOT
# ==============================================================================

class TimeSlot(HubBaseModel):
    """Available time windows per day of week."""

    DAYS_OF_WEEK = [
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    ]

    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_reservations = models.PositiveIntegerField(default=10, help_text=_('Maximum reservations for this slot'))
    is_active = models.BooleanField(default=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'reservations_timeslot'
        verbose_name = _('Time Slot')
        verbose_name_plural = _('Time Slots')
        ordering = ['day_of_week', 'start_time']
        constraints = [
            models.UniqueConstraint(fields=['hub_id', 'day_of_week', 'start_time', 'end_time'], name='unique_timeslot_per_hub'),
        ]

    def __str__(self):
        day_name = dict(self.DAYS_OF_WEEK).get(self.day_of_week, '?')
        return f'{day_name} {self.start_time:%H:%M}-{self.end_time:%H:%M}'

    @classmethod
    def get_slots_for_day(cls, hub_id, day_of_week):
        return cls.objects.filter(hub_id=hub_id, is_deleted=False, is_active=True, day_of_week=day_of_week).order_by('start_time')


# ==============================================================================
# BLOCKED DATE
# ==============================================================================

class BlockedDate(HubBaseModel):
    """Dates when reservations are not allowed (holidays, closures, etc.)."""

    date = models.DateField(db_index=True)
    reason = models.CharField(max_length=200, blank=True, default='')
    is_full_day = models.BooleanField(default=True, help_text=_('If false, only specific time range is blocked'))
    blocked_from = models.TimeField(null=True, blank=True)
    blocked_until = models.TimeField(null=True, blank=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'reservations_blockeddate'
        verbose_name = _('Blocked Date')
        verbose_name_plural = _('Blocked Dates')
        ordering = ['date']
        constraints = [
            models.UniqueConstraint(fields=['hub_id', 'date', 'blocked_from'], name='unique_blockeddate_per_hub'),
        ]

    def __str__(self):
        if self.is_full_day:
            return f'{self.date} — {self.reason or "Blocked"}'
        return f'{self.date} {self.blocked_from}-{self.blocked_until} — {self.reason or "Blocked"}'

    @classmethod
    def is_blocked(cls, hub_id, date, time=None):
        """Check if a date/time is blocked for a hub."""
        blocks = cls.objects.filter(hub_id=hub_id, date=date, is_deleted=False)
        for block in blocks:
            if block.is_full_day:
                return True
            if time and block.blocked_from and block.blocked_until:
                if block.blocked_from <= time <= block.blocked_until:
                    return True
        return False


# ==============================================================================
# RESERVATION
# ==============================================================================

class Reservation(HubBaseModel):
    """Individual reservation record."""

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('confirmed', _('Confirmed')),
        ('seated', _('Seated')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('no_show', _('No Show')),
    ]

    # Guest — either linked customer or manual entry
    customer = models.ForeignKey(
        'customers.Customer', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reservations',
    )
    guest_name = models.CharField(max_length=200)
    guest_phone = models.CharField(max_length=50, blank=True, default='')
    guest_email = models.EmailField(blank=True, default='')

    # Reservation details
    date = models.DateField(db_index=True)
    time = models.TimeField()
    party_size = models.PositiveIntegerField(default=2)
    duration_minutes = models.PositiveIntegerField(default=120, help_text=_('Expected duration in minutes'))

    # Table assignment
    table = models.ForeignKey(
        'tables.Table', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reservations',
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)

    # Notes
    notes = models.TextField(blank=True, default='', help_text=_('Special requests or notes'))
    internal_notes = models.TextField(blank=True, default='', help_text=_('Internal staff notes'))

    # Timestamps
    confirmed_at = models.DateTimeField(null=True, blank=True)
    seated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Cancellation
    cancellation_reason = models.TextField(blank=True, default='')

    class Meta(HubBaseModel.Meta):
        db_table = 'reservations_reservation'
        verbose_name = _('Reservation')
        verbose_name_plural = _('Reservations')
        ordering = ['date', 'time']
        indexes = [
            models.Index(fields=['hub_id', 'date', 'status']),
            models.Index(fields=['hub_id', 'guest_phone']),
        ]

    def __str__(self):
        return f'{self.guest_name} — {self.date} {self.time:%H:%M} ({self.party_size} guests)'

    # ── properties ───────────────────────────────────────────────────────

    @property
    def datetime(self):
        return timezone.make_aware(timezone.datetime.combine(self.date, self.time))

    @property
    def end_datetime(self):
        return self.datetime + timedelta(minutes=self.duration_minutes)

    @property
    def is_past(self):
        return self.datetime < timezone.now()

    @property
    def is_today(self):
        return self.date == timezone.now().date()

    @property
    def minutes_until(self):
        if self.is_past:
            return 0
        delta = self.datetime - timezone.now()
        return int(delta.total_seconds() / 60)

    @property
    def is_upcoming(self):
        return 0 < self.minutes_until <= 60

    @property
    def table_display(self):
        if self.table:
            return str(self.table)
        return ''

    @property
    def status_class(self):
        return {
            'pending': 'warning',
            'confirmed': 'primary',
            'seated': 'success',
            'completed': 'medium',
            'cancelled': 'danger',
            'no_show': 'dark',
        }.get(self.status, 'medium')

    @property
    def can_be_confirmed(self):
        return self.status == 'pending'

    @property
    def can_be_seated(self):
        return self.status in ('pending', 'confirmed')

    @property
    def can_be_completed(self):
        return self.status == 'seated'

    @property
    def can_be_cancelled(self):
        return self.status in ('pending', 'confirmed')

    # ── actions ──────────────────────────────────────────────────────────

    def confirm(self):
        if self.status != 'pending':
            return False
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        self.save(update_fields=['status', 'confirmed_at', 'updated_at'])
        return True

    def seat(self, table=None):
        if self.status not in ('pending', 'confirmed'):
            return False
        self.status = 'seated'
        self.seated_at = timezone.now()
        if table:
            self.table = table
        self.save(update_fields=['status', 'seated_at', 'table_id', 'updated_at'])
        return True

    def complete(self):
        if self.status != 'seated':
            return False
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])
        return True

    def cancel(self, reason=''):
        if self.status not in ('pending', 'confirmed'):
            return False
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save(update_fields=['status', 'cancelled_at', 'cancellation_reason', 'updated_at'])
        return True

    def mark_no_show(self):
        if self.status not in ('pending', 'confirmed'):
            return False
        self.status = 'no_show'
        self.save(update_fields=['status', 'updated_at'])
        return True

    # ── queries ──────────────────────────────────────────────────────────

    @classmethod
    def get_for_date(cls, hub_id, date):
        return cls.objects.filter(
            hub_id=hub_id, date=date, is_deleted=False,
        ).exclude(status__in=['cancelled', 'no_show']).order_by('time')

    @classmethod
    def get_upcoming(cls, hub_id, hours=2):
        now = timezone.now()
        return cls.objects.filter(
            hub_id=hub_id, date=now.date(), is_deleted=False,
            status__in=['pending', 'confirmed'],
        ).order_by('time')


# ==============================================================================
# WAITLIST
# ==============================================================================

class WaitlistEntry(HubBaseModel):
    """Waitlist for fully booked time slots."""

    guest_name = models.CharField(max_length=200)
    guest_phone = models.CharField(max_length=50)
    guest_email = models.EmailField(blank=True, default='')
    customer = models.ForeignKey(
        'customers.Customer', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='waitlist_entries',
    )
    date = models.DateField()
    preferred_time = models.TimeField()
    party_size = models.PositiveIntegerField(default=2)
    notes = models.TextField(blank=True, default='')
    is_contacted = models.BooleanField(default=False)
    is_converted = models.BooleanField(default=False, help_text=_('True if converted to a reservation'))
    reservation = models.ForeignKey(
        Reservation, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='waitlist_entries',
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'reservations_waitlistentry'
        verbose_name = _('Waitlist Entry')
        verbose_name_plural = _('Waitlist Entries')
        ordering = ['date', 'preferred_time', 'created_at']

    def __str__(self):
        return f'{self.guest_name} — {self.date} (waitlist)'

    def convert_to_reservation(self, settings=None):
        """Convert waitlist entry to a reservation."""
        if self.is_converted:
            return None
        duration = settings.default_duration_minutes if settings else 120
        status = 'confirmed' if (settings and settings.auto_confirm) else 'pending'
        reservation = Reservation.objects.create(
            hub_id=self.hub_id,
            guest_name=self.guest_name,
            guest_phone=self.guest_phone,
            guest_email=self.guest_email,
            customer=self.customer,
            date=self.date,
            time=self.preferred_time,
            party_size=self.party_size,
            notes=self.notes,
            status=status,
            duration_minutes=duration,
            confirmed_at=timezone.now() if status == 'confirmed' else None,
        )
        self.is_converted = True
        self.reservation = reservation
        self.save(update_fields=['is_converted', 'reservation', 'updated_at'])
        return reservation
