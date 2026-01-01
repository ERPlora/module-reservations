"""Reservations admin configuration."""

from django.contrib import admin
from .models import (
    ReservationsConfig,
    TimeSlot,
    Reservation,
    BlockedDate,
    WaitlistEntry
)


@admin.register(ReservationsConfig)
class ReservationsConfigAdmin(admin.ModelAdmin):
    """Admin for ReservationsConfig."""

    fieldsets = (
        ('Time Slots', {
            'fields': ('time_slot_duration', 'min_party_size', 'max_party_size')
        }),
        ('Advance Booking', {
            'fields': ('min_advance_hours', 'max_advance_days')
        }),
        ('Confirmation', {
            'fields': ('auto_confirm', 'require_phone', 'require_email')
        }),
        ('No-Show', {
            'fields': ('no_show_window_minutes', 'hold_table_minutes')
        }),
        ('Notifications', {
            'fields': ('send_confirmation_email', 'send_reminder_email', 'reminder_hours_before')
        }),
    )

    def has_add_permission(self, request):
        return not ReservationsConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    """Admin for TimeSlot."""

    list_display = ['day_of_week', 'start_time', 'end_time', 'max_reservations', 'is_active']
    list_filter = ['day_of_week', 'is_active']
    ordering = ['day_of_week', 'start_time']


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Admin for Reservation."""

    list_display = [
        'guest_name', 'date', 'time', 'party_size', 'status',
        'table_number', 'created_at'
    ]
    list_filter = ['status', 'date']
    search_fields = ['guest_name', 'guest_phone', 'guest_email']
    date_hierarchy = 'date'
    ordering = ['-date', '-time']

    fieldsets = (
        ('Guest Information', {
            'fields': ('guest_name', 'guest_phone', 'guest_email', 'customer_id')
        }),
        ('Reservation Details', {
            'fields': ('date', 'time', 'party_size', 'duration_minutes')
        }),
        ('Table', {
            'fields': ('table_id', 'table_number')
        }),
        ('Status', {
            'fields': ('status', 'cancellation_reason')
        }),
        ('Notes', {
            'fields': ('notes', 'internal_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'confirmed_at', 'seated_at', 'completed_at', 'cancelled_at'),
            'classes': ['collapse']
        }),
    )
    readonly_fields = ['created_at', 'confirmed_at', 'seated_at', 'completed_at', 'cancelled_at']


@admin.register(BlockedDate)
class BlockedDateAdmin(admin.ModelAdmin):
    """Admin for BlockedDate."""

    list_display = ['date', 'reason', 'is_full_day', 'blocked_from', 'blocked_until']
    list_filter = ['is_full_day']
    ordering = ['date']


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    """Admin for WaitlistEntry."""

    list_display = [
        'guest_name', 'date', 'preferred_time', 'party_size',
        'is_contacted', 'is_converted', 'created_at'
    ]
    list_filter = ['is_contacted', 'is_converted', 'date']
    search_fields = ['guest_name', 'guest_phone']
    ordering = ['date', 'preferred_time']
