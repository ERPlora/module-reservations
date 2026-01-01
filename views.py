"""Reservations views."""

import json
from datetime import datetime, timedelta

from django.db import models
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone

from apps.accounts.decorators import login_required

from .models import (
    Reservation,
    ReservationsConfig,
    TimeSlot,
    BlockedDate,
    WaitlistEntry
)


# ==============================================================================
# MAIN VIEWS
# ==============================================================================

@login_required
def index(request):
    """
    Main reservations view - today's reservations.
    """
    today = timezone.now().date()
    reservations = Reservation.get_for_date(today)

    # Group by status
    pending = reservations.filter(status=Reservation.STATUS_PENDING)
    confirmed = reservations.filter(status=Reservation.STATUS_CONFIRMED)
    seated = reservations.filter(status=Reservation.STATUS_SEATED)

    context = {
        'page_title': 'Today\'s Reservations',
        'page_type': 'list',
        'date': today,
        'reservations': reservations,
        'pending_count': pending.count(),
        'confirmed_count': confirmed.count(),
        'seated_count': seated.count(),
        'config': ReservationsConfig.get_config(),
    }
    return render(request, 'reservations/index.html', context)


@login_required
def calendar(request):
    """
    Calendar view for browsing reservations by date.
    """
    # Get date from query params or default to today
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    reservations = Reservation.get_for_date(selected_date)

    # Get blocked dates for the month
    first_of_month = selected_date.replace(day=1)
    if selected_date.month == 12:
        last_of_month = selected_date.replace(year=selected_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_of_month = selected_date.replace(month=selected_date.month + 1, day=1) - timedelta(days=1)

    blocked_dates = BlockedDate.objects.filter(
        date__gte=first_of_month,
        date__lte=last_of_month
    ).values_list('date', flat=True)

    context = {
        'page_title': 'Reservations Calendar',
        'page_type': 'list',
        'selected_date': selected_date,
        'reservations': reservations,
        'blocked_dates': list(blocked_dates),
    }
    return render(request, 'reservations/calendar.html', context)


@login_required
def reservation_list(request):
    """
    List all reservations with filters.
    """
    # Filter parameters
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')

    reservations = Reservation.objects.all()

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
        reservations = reservations.filter(guest_name__icontains=search)

    reservations = reservations.order_by('-date', '-time')[:100]

    context = {
        'page_title': 'All Reservations',
        'page_type': 'list',
        'reservations': reservations,
        'status_choices': Reservation.STATUS_CHOICES,
        'current_status': status,
        'current_search': search,
    }
    return render(request, 'reservations/list.html', context)


@login_required
def reservation_detail(request, reservation_id):
    """
    View reservation details.
    """
    reservation = get_object_or_404(Reservation, pk=reservation_id)

    context = {
        'page_title': f'Reservation - {reservation.guest_name}',
        'page_type': 'detail',
        'back_url': '/modules/reservations/',
        'reservation': reservation,
    }
    return render(request, 'reservations/detail.html', context)


@login_required
def reservation_create(request):
    """
    Create new reservation form.
    """
    config = ReservationsConfig.get_config()

    # Default to today's date
    default_date = timezone.now().date()
    default_time = timezone.now().replace(hour=19, minute=0, second=0, microsecond=0).time()

    context = {
        'page_title': 'New Reservation',
        'page_type': 'form',
        'back_url': '/modules/reservations/',
        'config': config,
        'default_date': default_date,
        'default_time': default_time,
    }
    return render(request, 'reservations/form.html', context)


@login_required
def reservation_edit(request, reservation_id):
    """
    Edit existing reservation.
    """
    reservation = get_object_or_404(Reservation, pk=reservation_id)
    config = ReservationsConfig.get_config()

    context = {
        'page_title': f'Edit Reservation - {reservation.guest_name}',
        'page_type': 'form',
        'back_url': f'/modules/reservations/{reservation_id}/',
        'reservation': reservation,
        'config': config,
    }
    return render(request, 'reservations/form.html', context)


@login_required
def waitlist(request):
    """
    View waitlist entries.
    """
    entries = WaitlistEntry.objects.filter(
        is_converted=False,
        date__gte=timezone.now().date()
    ).order_by('date', 'preferred_time')

    context = {
        'page_title': 'Waitlist',
        'page_type': 'list',
        'entries': entries,
    }
    return render(request, 'reservations/waitlist.html', context)


@login_required
def blocked_dates(request):
    """
    Manage blocked dates.
    """
    blocks = BlockedDate.objects.filter(
        date__gte=timezone.now().date()
    ).order_by('date')

    context = {
        'page_title': 'Blocked Dates',
        'page_type': 'list',
        'blocks': blocks,
    }
    return render(request, 'reservations/blocked_dates.html', context)


@login_required
def time_slots(request):
    """
    Manage time slots.
    """
    slots = TimeSlot.objects.all()

    context = {
        'page_title': 'Time Slots',
        'page_type': 'list',
        'slots': slots,
        'days_of_week': TimeSlot.DAYS_OF_WEEK,
    }
    return render(request, 'reservations/time_slots.html', context)


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@login_required
@require_POST
def api_create_reservation(request):
    """Create a new reservation."""
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST

        guest_name = data.get('guest_name', '').strip()
        guest_phone = data.get('guest_phone', '').strip()
        guest_email = data.get('guest_email', '').strip()
        date_str = data.get('date', '')
        time_str = data.get('time', '')
        party_size = int(data.get('party_size', 2))
        notes = data.get('notes', '').strip()

        if not guest_name:
            return JsonResponse({'success': False, 'error': 'Guest name is required'}, status=400)

        config = ReservationsConfig.get_config()
        if config.require_phone and not guest_phone:
            return JsonResponse({'success': False, 'error': 'Phone number is required'}, status=400)

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            time = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid date or time format'}, status=400)

        # Check if date is blocked
        if BlockedDate.is_blocked(date, time):
            return JsonResponse({'success': False, 'error': 'This date/time is not available'}, status=400)

        # Create reservation
        status = Reservation.STATUS_CONFIRMED if config.auto_confirm else Reservation.STATUS_PENDING
        reservation = Reservation.objects.create(
            guest_name=guest_name,
            guest_phone=guest_phone,
            guest_email=guest_email,
            date=date,
            time=time,
            party_size=party_size,
            notes=notes,
            status=status,
            duration_minutes=config.hold_table_minutes,
            confirmed_at=timezone.now() if config.auto_confirm else None,
        )

        return JsonResponse({
            'success': True,
            'reservation_id': reservation.id,
            'status': reservation.status,
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def api_update_reservation(request):
    """Update an existing reservation."""
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        reservation_id = data.get('reservation_id')

        reservation = get_object_or_404(Reservation, pk=reservation_id)

        # Update fields
        if 'guest_name' in data:
            reservation.guest_name = data['guest_name'].strip()
        if 'guest_phone' in data:
            reservation.guest_phone = data['guest_phone'].strip()
        if 'guest_email' in data:
            reservation.guest_email = data['guest_email'].strip()
        if 'date' in data:
            reservation.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if 'time' in data:
            reservation.time = datetime.strptime(data['time'], '%H:%M').time()
        if 'party_size' in data:
            reservation.party_size = int(data['party_size'])
        if 'notes' in data:
            reservation.notes = data['notes'].strip()
        if 'internal_notes' in data:
            reservation.internal_notes = data['internal_notes'].strip()
        if 'table_id' in data:
            reservation.table_id = data['table_id'] or None
        if 'table_number' in data:
            reservation.table_number = data['table_number']

        reservation.save()

        return JsonResponse({
            'success': True,
            'reservation_id': reservation.id,
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def api_confirm_reservation(request):
    """Confirm a pending reservation."""
    reservation_id = request.POST.get('reservation_id')
    reservation = get_object_or_404(Reservation, pk=reservation_id)

    if reservation.confirm():
        return JsonResponse({
            'success': True,
            'status': reservation.status,
        })
    return JsonResponse({
        'success': False,
        'error': 'Cannot confirm reservation in current status'
    }, status=400)


@login_required
@require_POST
def api_seat_reservation(request):
    """Mark reservation as seated."""
    reservation_id = request.POST.get('reservation_id')
    table_id = request.POST.get('table_id')
    table_number = request.POST.get('table_number', '')

    reservation = get_object_or_404(Reservation, pk=reservation_id)

    if reservation.seat(table_id=table_id, table_number=table_number):
        return JsonResponse({
            'success': True,
            'status': reservation.status,
        })
    return JsonResponse({
        'success': False,
        'error': 'Cannot seat reservation in current status'
    }, status=400)


@login_required
@require_POST
def api_complete_reservation(request):
    """Mark reservation as completed."""
    reservation_id = request.POST.get('reservation_id')
    reservation = get_object_or_404(Reservation, pk=reservation_id)

    if reservation.complete():
        return JsonResponse({
            'success': True,
            'status': reservation.status,
        })
    return JsonResponse({
        'success': False,
        'error': 'Cannot complete reservation in current status'
    }, status=400)


@login_required
@require_POST
def api_cancel_reservation(request):
    """Cancel a reservation."""
    reservation_id = request.POST.get('reservation_id')
    reason = request.POST.get('reason', '')
    reservation = get_object_or_404(Reservation, pk=reservation_id)

    if reservation.cancel(reason=reason):
        return JsonResponse({
            'success': True,
            'status': reservation.status,
        })
    return JsonResponse({
        'success': False,
        'error': 'Cannot cancel reservation in current status'
    }, status=400)


@login_required
@require_POST
def api_no_show_reservation(request):
    """Mark reservation as no-show."""
    reservation_id = request.POST.get('reservation_id')
    reservation = get_object_or_404(Reservation, pk=reservation_id)

    if reservation.mark_no_show():
        return JsonResponse({
            'success': True,
            'status': reservation.status,
        })
    return JsonResponse({
        'success': False,
        'error': 'Cannot mark as no-show in current status'
    }, status=400)


@login_required
@require_GET
def api_reservations_for_date(request):
    """Get reservations for a specific date."""
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'success': False, 'error': 'Date required'}, status=400)

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid date format'}, status=400)

    reservations = Reservation.get_for_date(date)

    return JsonResponse({
        'success': True,
        'date': date_str,
        'reservations': [
            {
                'id': r.id,
                'guest_name': r.guest_name,
                'time': r.time.strftime('%H:%M'),
                'party_size': r.party_size,
                'status': r.status,
                'table_number': r.table_number,
            }
            for r in reservations
        ]
    })


@login_required
@require_GET
def api_check_availability(request):
    """Check availability for a date/time."""
    date_str = request.GET.get('date')
    time_str = request.GET.get('time')
    party_size = int(request.GET.get('party_size', 2))

    if not date_str or not time_str:
        return JsonResponse({'success': False, 'error': 'Date and time required'}, status=400)

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        time = datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid date/time format'}, status=400)

    # Check if blocked
    is_blocked = BlockedDate.is_blocked(date, time)

    # Count existing reservations for that time slot
    existing = Reservation.objects.filter(
        date=date,
        time=time,
        status__in=[Reservation.STATUS_PENDING, Reservation.STATUS_CONFIRMED]
    ).count()

    return JsonResponse({
        'success': True,
        'available': not is_blocked,
        'existing_count': existing,
        'is_blocked': is_blocked,
    })


@login_required
@require_POST
def api_add_to_waitlist(request):
    """Add entry to waitlist."""
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST

        entry = WaitlistEntry.objects.create(
            guest_name=data.get('guest_name', '').strip(),
            guest_phone=data.get('guest_phone', '').strip(),
            guest_email=data.get('guest_email', '').strip(),
            date=datetime.strptime(data.get('date'), '%Y-%m-%d').date(),
            preferred_time=datetime.strptime(data.get('time'), '%H:%M').time(),
            party_size=int(data.get('party_size', 2)),
            notes=data.get('notes', '').strip(),
        )

        return JsonResponse({
            'success': True,
            'entry_id': entry.id,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def api_convert_waitlist(request):
    """Convert waitlist entry to reservation."""
    entry_id = request.POST.get('entry_id')
    entry = get_object_or_404(WaitlistEntry, pk=entry_id)

    reservation = entry.convert_to_reservation()
    if reservation:
        return JsonResponse({
            'success': True,
            'reservation_id': reservation.id,
        })
    return JsonResponse({
        'success': False,
        'error': 'Entry already converted'
    }, status=400)


@login_required
@require_POST
def api_block_date(request):
    """Block a date."""
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST

        date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
        reason = data.get('reason', '').strip()
        is_full_day = data.get('is_full_day', 'true').lower() == 'true'

        block = BlockedDate.objects.create(
            date=date,
            reason=reason,
            is_full_day=is_full_day,
        )

        return JsonResponse({
            'success': True,
            'block_id': block.id,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def api_unblock_date(request):
    """Unblock a date."""
    block_id = request.POST.get('block_id')
    block = get_object_or_404(BlockedDate, pk=block_id)
    block.delete()

    return JsonResponse({'success': True})


# ==============================================================================
# SETTINGS VIEWS
# ==============================================================================

@login_required
def reservations_settings(request):
    """
    Reservations settings page.
    """
    config = ReservationsConfig.get_config()

    context = {
        'page_title': 'Reservations Settings',
        'page_type': 'form',
        'back_url': '/modules/reservations/',
        'config': config,
    }
    return render(request, 'reservations/settings.html', context)


@login_required
@require_POST
def reservations_settings_save(request):
    """Save all settings at once."""
    try:
        data = json.loads(request.body)
        config = ReservationsConfig.get_config()

        # Update all fields
        for field, value in data.items():
            if hasattr(config, field):
                setattr(config, field, value)

        config.save()
        return JsonResponse({'success': True})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)


@login_required
@require_POST
def reservations_settings_toggle(request):
    """Toggle a boolean setting."""
    name = request.POST.get('name')
    value = request.POST.get('value', '').lower() == 'true'

    config = ReservationsConfig.get_config()
    if hasattr(config, name):
        setattr(config, name, value)
        config.save()

    return JsonResponse({}, status=204)


@login_required
@require_POST
def reservations_settings_input(request):
    """Update a numeric or text setting."""
    name = request.POST.get('name')
    value = request.POST.get('value')

    config = ReservationsConfig.get_config()
    if hasattr(config, name):
        field = config._meta.get_field(name)
        if isinstance(field, models.IntegerField):
            value = int(value)
        setattr(config, name, value)
        config.save()

    return JsonResponse({}, status=204)


@login_required
@require_POST
def reservations_settings_reset(request):
    """Reset settings to defaults."""
    config = ReservationsConfig.get_config()

    # Reset to defaults
    config.time_slot_duration = 30
    config.min_party_size = 1
    config.max_party_size = 20
    config.min_advance_hours = 1
    config.max_advance_days = 30
    config.auto_confirm = False
    config.require_phone = True
    config.require_email = False
    config.no_show_window_minutes = 15
    config.hold_table_minutes = 120
    config.send_confirmation_email = False
    config.send_reminder_email = False
    config.reminder_hours_before = 24
    config.save()

    return JsonResponse({}, status=204)
