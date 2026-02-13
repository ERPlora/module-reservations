"""Reservations forms."""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    Reservation,
    ReservationSettings,
    TimeSlot,
    BlockedDate,
    WaitlistEntry,
)


class ReservationForm(forms.ModelForm):
    """Full reservation form."""

    class Meta:
        model = Reservation
        fields = [
            'guest_name', 'guest_phone', 'guest_email', 'customer',
            'date', 'time', 'party_size', 'duration_minutes',
            'table', 'notes', 'internal_notes',
        ]
        widgets = {
            'guest_name': forms.TextInput(attrs={'class': 'input', 'placeholder': _('Guest name')}),
            'guest_phone': forms.TextInput(attrs={'class': 'input', 'placeholder': _('Phone'), 'type': 'tel'}),
            'guest_email': forms.EmailInput(attrs={'class': 'input', 'placeholder': _('Email')}),
            'customer': forms.Select(attrs={'class': 'select'}),
            'date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
            'party_size': forms.NumberInput(attrs={'class': 'input', 'min': 1, 'max': 50}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'input', 'min': 15, 'step': 15}),
            'table': forms.Select(attrs={'class': 'select'}),
            'notes': forms.Textarea(attrs={'class': 'textarea', 'rows': 3, 'placeholder': _('Special requests')}),
            'internal_notes': forms.Textarea(attrs={'class': 'textarea', 'rows': 2, 'placeholder': _('Internal notes')}),
        }


class ReservationQuickForm(forms.ModelForm):
    """Simplified form for quick reservations."""

    class Meta:
        model = Reservation
        fields = ['guest_name', 'guest_phone', 'date', 'time', 'party_size', 'notes']
        widgets = {
            'guest_name': forms.TextInput(attrs={'class': 'input', 'placeholder': _('Guest name')}),
            'guest_phone': forms.TextInput(attrs={'class': 'input', 'placeholder': _('Phone'), 'type': 'tel'}),
            'date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
            'party_size': forms.NumberInput(attrs={'class': 'input', 'min': 1, 'max': 50}),
            'notes': forms.Textarea(attrs={'class': 'textarea', 'rows': 2, 'placeholder': _('Notes')}),
        }


class TimeSlotForm(forms.ModelForm):
    """Form for managing time slots."""

    class Meta:
        model = TimeSlot
        fields = ['day_of_week', 'start_time', 'end_time', 'max_reservations', 'is_active']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'select'}),
            'start_time': forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
            'max_reservations': forms.NumberInput(attrs={'class': 'input', 'min': 1}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle'}),
        }


class BlockedDateForm(forms.ModelForm):
    """Form for blocking dates."""

    class Meta:
        model = BlockedDate
        fields = ['date', 'reason', 'is_full_day', 'blocked_from', 'blocked_until']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'reason': forms.TextInput(attrs={'class': 'input', 'placeholder': _('Reason')}),
            'is_full_day': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'blocked_from': forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
            'blocked_until': forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
        }


class WaitlistForm(forms.ModelForm):
    """Form for waitlist entries."""

    class Meta:
        model = WaitlistEntry
        fields = ['guest_name', 'guest_phone', 'guest_email', 'customer', 'date', 'preferred_time', 'party_size', 'notes']
        widgets = {
            'guest_name': forms.TextInput(attrs={'class': 'input', 'placeholder': _('Guest name')}),
            'guest_phone': forms.TextInput(attrs={'class': 'input', 'placeholder': _('Phone'), 'type': 'tel'}),
            'guest_email': forms.EmailInput(attrs={'class': 'input', 'placeholder': _('Email')}),
            'customer': forms.Select(attrs={'class': 'select'}),
            'date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'preferred_time': forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
            'party_size': forms.NumberInput(attrs={'class': 'input', 'min': 1, 'max': 50}),
            'notes': forms.Textarea(attrs={'class': 'textarea', 'rows': 2, 'placeholder': _('Notes')}),
        }


class ReservationFilterForm(forms.Form):
    """Form for filtering reservations list."""

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': _('Search guests...')}),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', _('All statuses'))] + Reservation.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'select'}),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
    )


class ReservationSettingsForm(forms.ModelForm):
    """Form for editing reservation settings."""

    class Meta:
        model = ReservationSettings
        fields = [
            'time_slot_duration', 'min_party_size', 'max_party_size',
            'min_advance_hours', 'max_advance_days',
            'auto_confirm', 'require_phone', 'require_email',
            'no_show_window_minutes', 'default_duration_minutes',
            'send_confirmation_email', 'send_reminder_email', 'reminder_hours_before',
        ]
        widgets = {
            'time_slot_duration': forms.NumberInput(attrs={'class': 'input', 'min': 5, 'step': 5}),
            'min_party_size': forms.NumberInput(attrs={'class': 'input', 'min': 1}),
            'max_party_size': forms.NumberInput(attrs={'class': 'input', 'min': 1}),
            'min_advance_hours': forms.NumberInput(attrs={'class': 'input', 'min': 0}),
            'max_advance_days': forms.NumberInput(attrs={'class': 'input', 'min': 1}),
            'auto_confirm': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'require_phone': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'require_email': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'no_show_window_minutes': forms.NumberInput(attrs={'class': 'input', 'min': 5}),
            'default_duration_minutes': forms.NumberInput(attrs={'class': 'input', 'min': 15, 'step': 15}),
            'send_confirmation_email': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'send_reminder_email': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'reminder_hours_before': forms.NumberInput(attrs={'class': 'input', 'min': 1}),
        }
