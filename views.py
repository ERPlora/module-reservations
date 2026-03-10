"""Reservations views.

Sections: Today, Calendar, List, Waitlist, Availability (time slots + blocked dates),
CRUD, Status actions, API, Settings.
"""

import json
from datetime import datetime, timedelta

from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from django.utils.translation import gettext as _
from django.utils import timezone

from apps.accounts.decorators import login_required, permission_required
from apps.core.htmx import htmx_view

from .models import (
    Reservation,
    ReservationSettings,
    TimeSlot,
    BlockedDate,
    WaitlistEntry,
)
from .forms import (
    ReservationForm,
    ReservationQuickForm,
    TimeSlotForm,
    BlockedDateForm,
    WaitlistForm,
    ReservationFilterForm,
    ReservationSettingsForm,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _hub(request):
    return request.session.get('hub_id')


def _employee(request):
    from apps.accounts.models import LocalUser
    uid = request.session.get('local_user_id')
    if uid:
        return LocalUser.objects.filter(pk=uid).first()
    return None


def is_setup_complete():
    """Check if reservations module has been set up (at least 1 time slot)."""
    return TimeSlot.objects.filter(is_deleted=False).exists()


@login_required
def setup(request):
    """Initial setup: AI-powered time slot configuration."""
    from django.shortcuts import render, redirect

    if is_setup_complete():
        return redirect('/m/reservations/')

    from apps.configuration.models import StoreConfig
    store = StoreConfig.get_config()
    business = store.business_name or _('your business')

    welcome = str(_(
        "I'll help you set up your reservation schedule. Tell me about your "
        "opening hours - when do you serve lunch? Dinner? Are there any days "
        "you're closed?"
    ))
    auto_prompt = json.dumps(str(_(
        "I need to set up reservation time slots for %(business)s. "
        "Please load the reservations module tools and ask me about my schedule."
    ) % {'business': business}))

    return render(request, 'reservations/pages/setup.html', {
        'welcome_message': welcome,
        'auto_prompt': auto_prompt,
    })


# ==============================================================================
# INDEX / TODAY
# ==============================================================================

@login_required
@htmx_view('reservations/pages/index.html', 'reservations/partials/index.html')
def index(request):
    """Redirect to today view."""
    return today(request)


@login_required
@htmx_view('reservations/pages/today.html', 'reservations/partials/today.html')
def today(request):
    """Today's reservations grouped by status."""
    hub = _hub(request)
    today_date = timezone.now().date()
    reservations = Reservation.get_for_date(hub, today_date)

    pending = reservations.filter(status='pending')
    confirmed = reservations.filter(status='confirmed')
    seated = reservations.filter(status='seated')
    upcoming = Reservation.get_upcoming(hub)

    return {
        'date': today_date,
        'reservations': reservations,
        'pending_count': pending.count(),
        'confirmed_count': confirmed.count(),
        'seated_count': seated.count(),
        'upcoming': upcoming,
        'settings': ReservationSettings.get_settings(hub),
    }


# ==============================================================================
# CALENDAR
# ==============================================================================

@login_required
@htmx_view('reservations/pages/calendar.html', 'reservations/partials/calendar.html')
def calendar(request):
    """Calendar view for browsing reservations by date."""
    hub = _hub(request)
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    reservations = Reservation.get_for_date(hub, selected_date)

    # Blocked dates for the month
    first_of_month = selected_date.replace(day=1)
    if selected_date.month == 12:
        last_of_month = selected_date.replace(year=selected_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_of_month = selected_date.replace(month=selected_date.month + 1, day=1) - timedelta(days=1)

    blocked_dates = BlockedDate.objects.filter(
        hub_id=hub, is_deleted=False,
        date__gte=first_of_month, date__lte=last_of_month,
    ).values_list('date', flat=True)

    return {
        'selected_date': selected_date,
        'reservations': reservations,
        'blocked_dates': list(blocked_dates),
    }


# ==============================================================================
# LIST
# ==============================================================================

@login_required
@htmx_view('reservations/pages/list.html', 'reservations/partials/list.html')
def reservation_list(request):
    """All reservations with filters."""
    hub = _hub(request)
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('q', '').strip()

    reservations = Reservation.objects.filter(hub_id=hub, is_deleted=False)

    if status:
        reservations = reservations.filter(status=status)
    if date_from:
        try:
            reservations = reservations.filter(date__gte=datetime.strptime(date_from, '%Y-%m-%d').date())
        except ValueError:
            pass
    if date_to:
        try:
            reservations = reservations.filter(date__lte=datetime.strptime(date_to, '%Y-%m-%d').date())
        except ValueError:
            pass
    if search:
        reservations = reservations.filter(
            Q(guest_name__icontains=search) |
            Q(guest_phone__icontains=search) |
            Q(guest_email__icontains=search)
        )

    reservations = reservations.select_related('table', 'customer').order_by('-date', '-time')[:100]

    return {
        'reservations': reservations,
        'status_choices': Reservation.STATUS_CHOICES,
        'current_status': status,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'filter_form': ReservationFilterForm(request.GET),
    }


# ==============================================================================
# CRUD
# ==============================================================================

@login_required
@htmx_view('reservations/pages/detail.html', 'reservations/partials/detail.html')
def reservation_detail(request, pk):
    """View reservation detail."""
    hub = _hub(request)
    reservation = get_object_or_404(Reservation, pk=pk, hub_id=hub, is_deleted=False)
    waitlist = reservation.waitlist_entries.filter(is_deleted=False)

    return {'reservation': reservation, 'waitlist_entries': waitlist}


@login_required
@htmx_view('reservations/pages/form.html', 'reservations/partials/form.html')
def reservation_create(request):
    """Create new reservation."""
    hub = _hub(request)
    settings = ReservationSettings.get_settings(hub)

    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.hub_id = hub
            reservation.duration_minutes = settings.default_duration_minutes

            if settings.auto_confirm:
                reservation.status = 'confirmed'
                reservation.confirmed_at = timezone.now()

            # Check if blocked
            if BlockedDate.is_blocked(hub, reservation.date, reservation.time):
                form.add_error(None, _('This date/time is not available'))
                return {'form': form, 'settings': settings}

            reservation.save()
            return JsonResponse({'success': True, 'id': str(reservation.pk)})
        return {'form': form, 'settings': settings}

    form = ReservationForm(initial={
        'date': timezone.now().date(),
        'time': '19:00',
        'party_size': 2,
    })
    return {'form': form, 'settings': settings}


@login_required
@htmx_view('reservations/pages/form.html', 'reservations/partials/form.html')
def reservation_edit(request, pk):
    """Edit existing reservation."""
    hub = _hub(request)
    reservation = get_object_or_404(Reservation, pk=pk, hub_id=hub, is_deleted=False)
    settings = ReservationSettings.get_settings(hub)

    if request.method == 'POST':
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'id': str(reservation.pk)})
        return {'form': form, 'reservation': reservation, 'settings': settings}

    form = ReservationForm(instance=reservation)
    return {'form': form, 'reservation': reservation, 'settings': settings}


@login_required
@require_POST
def reservation_delete(request, pk):
    """Soft-delete a reservation."""
    hub = _hub(request)
    reservation = get_object_or_404(Reservation, pk=pk, hub_id=hub, is_deleted=False)
    reservation.is_deleted = True
    reservation.deleted_at = timezone.now()
    reservation.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True})


# ==============================================================================
# STATUS ACTIONS
# ==============================================================================

@login_required
@require_POST
def confirm_reservation(request, pk):
    hub = _hub(request)
    reservation = get_object_or_404(Reservation, pk=pk, hub_id=hub, is_deleted=False)
    if reservation.confirm():
        return JsonResponse({'success': True, 'status': reservation.status})
    return JsonResponse({'success': False, 'error': _('Cannot confirm reservation')}, status=400)


@login_required
@require_POST
def seat_reservation(request, pk):
    hub = _hub(request)
    reservation = get_object_or_404(Reservation, pk=pk, hub_id=hub, is_deleted=False)
    table_id = request.POST.get('table_id')
    table = None
    if table_id:
        from tables.models import Table
        table = Table.objects.filter(pk=table_id, hub_id=hub, is_deleted=False).first()
    if reservation.seat(table=table):
        return JsonResponse({'success': True, 'status': reservation.status})
    return JsonResponse({'success': False, 'error': _('Cannot seat reservation')}, status=400)


@login_required
@require_POST
def complete_reservation(request, pk):
    hub = _hub(request)
    reservation = get_object_or_404(Reservation, pk=pk, hub_id=hub, is_deleted=False)
    if reservation.complete():
        return JsonResponse({'success': True, 'status': reservation.status})
    return JsonResponse({'success': False, 'error': _('Cannot complete reservation')}, status=400)


@login_required
@require_POST
def cancel_reservation(request, pk):
    hub = _hub(request)
    reservation = get_object_or_404(Reservation, pk=pk, hub_id=hub, is_deleted=False)
    reason = request.POST.get('reason', '')
    if reservation.cancel(reason=reason):
        return JsonResponse({'success': True, 'status': reservation.status})
    return JsonResponse({'success': False, 'error': _('Cannot cancel reservation')}, status=400)


@login_required
@require_POST
def no_show_reservation(request, pk):
    hub = _hub(request)
    reservation = get_object_or_404(Reservation, pk=pk, hub_id=hub, is_deleted=False)
    if reservation.mark_no_show():
        return JsonResponse({'success': True, 'status': reservation.status})
    return JsonResponse({'success': False, 'error': _('Cannot mark as no-show')}, status=400)


# ==============================================================================
# WAITLIST
# ==============================================================================

@login_required
@htmx_view('reservations/pages/waitlist.html', 'reservations/partials/waitlist.html')
def waitlist(request):
    """View waitlist entries."""
    hub = _hub(request)
    entries = WaitlistEntry.objects.filter(
        hub_id=hub, is_deleted=False, is_converted=False,
        date__gte=timezone.now().date(),
    ).select_related('customer').order_by('date', 'preferred_time')

    return {'entries': entries}


@login_required
@require_POST
def waitlist_add(request):
    """Add entry to waitlist."""
    hub = _hub(request)
    form = WaitlistForm(request.POST)
    if form.is_valid():
        entry = form.save(commit=False)
        entry.hub_id = hub
        entry.save()
        return JsonResponse({'success': True, 'id': str(entry.pk)})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
@require_POST
def waitlist_convert(request, pk):
    """Convert waitlist entry to reservation."""
    hub = _hub(request)
    entry = get_object_or_404(WaitlistEntry, pk=pk, hub_id=hub, is_deleted=False)
    settings = ReservationSettings.get_settings(hub)
    reservation = entry.convert_to_reservation(settings=settings)
    if reservation:
        return JsonResponse({'success': True, 'reservation_id': str(reservation.pk)})
    return JsonResponse({'success': False, 'error': _('Entry already converted')}, status=400)


@login_required
@require_POST
def waitlist_delete(request, pk):
    """Remove waitlist entry."""
    hub = _hub(request)
    entry = get_object_or_404(WaitlistEntry, pk=pk, hub_id=hub, is_deleted=False)
    entry.is_deleted = True
    entry.deleted_at = timezone.now()
    entry.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True})


# ==============================================================================
# AVAILABILITY (time slots + blocked dates)
# ==============================================================================

@login_required
@htmx_view('reservations/pages/availability.html', 'reservations/partials/availability.html')
def availability(request):
    """Manage time slots and blocked dates."""
    hub = _hub(request)
    slots = TimeSlot.objects.filter(hub_id=hub, is_deleted=False).order_by('day_of_week', 'start_time')
    blocked = BlockedDate.objects.filter(
        hub_id=hub, is_deleted=False, date__gte=timezone.now().date(),
    ).order_by('date')

    return {'slots': slots, 'blocked_dates': blocked, 'days_of_week': TimeSlot.DAYS_OF_WEEK}


@login_required
@require_POST
def timeslot_add(request):
    """Add a time slot."""
    hub = _hub(request)
    form = TimeSlotForm(request.POST)
    if form.is_valid():
        slot = form.save(commit=False)
        slot.hub_id = hub
        slot.save()
        return JsonResponse({'success': True, 'id': str(slot.pk)})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
@require_POST
def timeslot_edit(request, pk):
    """Edit a time slot."""
    hub = _hub(request)
    slot = get_object_or_404(TimeSlot, pk=pk, hub_id=hub, is_deleted=False)
    form = TimeSlotForm(request.POST, instance=slot)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
@require_POST
def timeslot_delete(request, pk):
    """Delete a time slot."""
    hub = _hub(request)
    slot = get_object_or_404(TimeSlot, pk=pk, hub_id=hub, is_deleted=False)
    slot.is_deleted = True
    slot.deleted_at = timezone.now()
    slot.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True})


@login_required
@require_POST
def blocked_date_add(request):
    """Block a date."""
    hub = _hub(request)
    form = BlockedDateForm(request.POST)
    if form.is_valid():
        block = form.save(commit=False)
        block.hub_id = hub
        block.save()
        return JsonResponse({'success': True, 'id': str(block.pk)})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
@require_POST
def blocked_date_delete(request, pk):
    """Unblock a date."""
    hub = _hub(request)
    block = get_object_or_404(BlockedDate, pk=pk, hub_id=hub, is_deleted=False)
    block.is_deleted = True
    block.deleted_at = timezone.now()
    block.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return JsonResponse({'success': True})


# ==============================================================================
# API
# ==============================================================================

@login_required
@require_GET
def api_reservations_for_date(request):
    """Get reservations for a specific date."""
    hub = _hub(request)
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'success': False, 'error': _('Date required')}, status=400)

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'success': False, 'error': _('Invalid date format')}, status=400)

    reservations = Reservation.get_for_date(hub, date)

    return JsonResponse({
        'success': True,
        'date': date_str,
        'reservations': [
            {
                'id': str(r.pk),
                'guest_name': r.guest_name,
                'time': r.time.strftime('%H:%M'),
                'party_size': r.party_size,
                'status': r.status,
                'table': r.table_display,
            }
            for r in reservations
        ],
    })


@login_required
@require_GET
def api_check_availability(request):
    """Check availability for a date/time."""
    hub = _hub(request)
    date_str = request.GET.get('date')
    time_str = request.GET.get('time')
    party_size = int(request.GET.get('party_size', 2))

    if not date_str or not time_str:
        return JsonResponse({'success': False, 'error': _('Date and time required')}, status=400)

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        time = datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        return JsonResponse({'success': False, 'error': _('Invalid date/time format')}, status=400)

    blocked = BlockedDate.is_blocked(hub, date, time)
    existing = Reservation.objects.filter(
        hub_id=hub, date=date, time=time, is_deleted=False,
        status__in=['pending', 'confirmed'],
    ).count()

    return JsonResponse({
        'success': True,
        'available': not blocked,
        'existing_count': existing,
        'is_blocked': blocked,
    })


# ==============================================================================
# SETTINGS
# ==============================================================================

@login_required
@permission_required('reservations.manage_settings')
@htmx_view('reservations/pages/settings.html', 'reservations/partials/settings.html')
def settings(request):
    """Reservation settings page."""
    hub = _hub(request)
    config = ReservationSettings.get_settings(hub)
    return {'config': config, 'form': ReservationSettingsForm(instance=config)}


@login_required
@permission_required('reservations.manage_settings')
@require_POST
def settings_save(request):
    """Save all settings."""
    hub = _hub(request)
    try:
        data = json.loads(request.body)
        config = ReservationSettings.get_settings(hub)

        for field in [
            'auto_confirm', 'require_phone', 'require_email',
            'send_confirmation_email', 'send_reminder_email',
        ]:
            if field in data:
                setattr(config, field, bool(data[field]))

        for field in [
            'time_slot_duration', 'min_party_size', 'max_party_size',
            'min_advance_hours', 'max_advance_days',
            'no_show_window_minutes', 'default_duration_minutes',
            'reminder_hours_before',
        ]:
            if field in data:
                try:
                    setattr(config, field, int(data[field]))
                except (ValueError, TypeError):
                    pass

        config.save()
        return JsonResponse({'success': True, 'message': _('Settings saved')})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': _('Invalid JSON')}, status=400)


@login_required
@permission_required('reservations.manage_settings')
@require_POST
def settings_toggle(request):
    """Toggle a boolean setting."""
    hub = _hub(request)
    name = request.POST.get('name') or request.POST.get('setting_name')
    value = request.POST.get('value', request.POST.get('setting_value', 'false'))
    setting_value = value == 'true' or value is True

    config = ReservationSettings.get_settings(hub)
    boolean_fields = [
        'auto_confirm', 'require_phone', 'require_email',
        'send_confirmation_email', 'send_reminder_email',
    ]
    if name in boolean_fields:
        setattr(config, name, setting_value)
        config.save()

    response = HttpResponse(status=204)
    response['HX-Trigger'] = json.dumps({
        'showToast': {'message': str(_('Setting updated')), 'color': 'success'}
    })
    return response


@login_required
@require_POST
def settings_input(request):
    """Update a numeric setting."""
    hub = _hub(request)
    name = request.POST.get('name') or request.POST.get('setting_name')
    value = request.POST.get('value') or request.POST.get('setting_value')

    config = ReservationSettings.get_settings(hub)
    numeric_fields = [
        'time_slot_duration', 'min_party_size', 'max_party_size',
        'min_advance_hours', 'max_advance_days',
        'no_show_window_minutes', 'default_duration_minutes',
        'reminder_hours_before',
    ]
    if name in numeric_fields:
        try:
            setattr(config, name, int(value))
            config.save()
        except (ValueError, TypeError):
            pass

    response = HttpResponse(status=204)
    response['HX-Trigger'] = json.dumps({
        'showToast': {'message': str(_('Setting updated')), 'color': 'success'}
    })
    return response


@login_required
@require_POST
def settings_reset(request):
    """Reset settings to defaults."""
    hub = _hub(request)
    config = ReservationSettings.get_settings(hub)

    config.time_slot_duration = 30
    config.min_party_size = 1
    config.max_party_size = 20
    config.min_advance_hours = 1
    config.max_advance_days = 30
    config.auto_confirm = False
    config.require_phone = True
    config.require_email = False
    config.no_show_window_minutes = 15
    config.default_duration_minutes = 120
    config.send_confirmation_email = False
    config.send_reminder_email = False
    config.reminder_hours_before = 24
    config.save()

    response = HttpResponse(status=204)
    response['HX-Trigger'] = json.dumps({
        'showToast': {'message': str(_('Settings reset to defaults')), 'color': 'warning'},
        'refreshPage': True,
    })
    return response
