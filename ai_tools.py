"""AI tools for the Reservations module."""
from assistant.tools import AssistantTool, register_tool


@register_tool
class ListReservations(AssistantTool):
    name = "list_reservations"
    description = "List reservations with filters. Returns guest, date, time, party size, status, table."
    module_id = "reservations"
    required_permission = "reservations.view_reservation"
    parameters = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "Filter: pending, confirmed, seated, completed, cancelled, no_show"},
            "date": {"type": "string", "description": "Filter by date (YYYY-MM-DD)"},
            "limit": {"type": "integer", "description": "Max results (default 20)"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from reservations.models import Reservation
        qs = Reservation.objects.select_related('table', 'customer').all()
        if args.get('status'):
            qs = qs.filter(status=args['status'])
        if args.get('date'):
            qs = qs.filter(date=args['date'])
        limit = args.get('limit', 20)
        return {
            "reservations": [
                {
                    "id": str(r.id),
                    "guest_name": r.guest_name,
                    "guest_phone": r.guest_phone,
                    "date": str(r.date),
                    "time": str(r.time),
                    "party_size": r.party_size,
                    "duration_minutes": r.duration_minutes,
                    "status": r.status,
                    "table": r.table.number if r.table else None,
                    "notes": r.notes,
                }
                for r in qs.order_by('date', 'time')[:limit]
            ],
            "total": qs.count(),
        }


@register_tool
class CreateReservation(AssistantTool):
    name = "create_reservation"
    description = "Create a new reservation."
    module_id = "reservations"
    required_permission = "reservations.add_reservation"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "guest_name": {"type": "string", "description": "Guest name"},
            "guest_phone": {"type": "string", "description": "Guest phone"},
            "guest_email": {"type": "string", "description": "Guest email"},
            "date": {"type": "string", "description": "Date (YYYY-MM-DD)"},
            "time": {"type": "string", "description": "Time (HH:MM)"},
            "party_size": {"type": "integer", "description": "Number of guests"},
            "duration_minutes": {"type": "integer", "description": "Duration in minutes"},
            "table_id": {"type": "string", "description": "Table ID"},
            "notes": {"type": "string", "description": "Notes"},
        },
        "required": ["guest_name", "date", "time", "party_size"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from reservations.models import Reservation
        r = Reservation.objects.create(
            guest_name=args['guest_name'],
            guest_phone=args.get('guest_phone', ''),
            guest_email=args.get('guest_email', ''),
            date=args['date'],
            time=args['time'],
            party_size=args['party_size'],
            duration_minutes=args.get('duration_minutes', 90),
            table_id=args.get('table_id'),
            notes=args.get('notes', ''),
        )
        return {"id": str(r.id), "guest_name": r.guest_name, "date": str(r.date), "created": True}


@register_tool
class UpdateReservationStatus(AssistantTool):
    name = "update_reservation_status"
    description = "Update reservation status: confirm, seat, complete, cancel, no_show."
    module_id = "reservations"
    required_permission = "reservations.change_reservation"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "reservation_id": {"type": "string", "description": "Reservation ID"},
            "status": {"type": "string", "description": "New status: confirmed, seated, completed, cancelled, no_show"},
            "cancellation_reason": {"type": "string", "description": "Reason for cancellation"},
        },
        "required": ["reservation_id", "status"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from reservations.models import Reservation
        from django.utils import timezone
        r = Reservation.objects.get(id=args['reservation_id'])
        r.status = args['status']
        if args['status'] == 'confirmed':
            r.confirmed_at = timezone.now()
        elif args['status'] == 'seated':
            r.seated_at = timezone.now()
        elif args['status'] == 'cancelled':
            r.cancelled_at = timezone.now()
            r.cancellation_reason = args.get('cancellation_reason', '')
        r.save()
        return {"id": str(r.id), "status": r.status, "updated": True}


@register_tool
class ListTimeSlots(AssistantTool):
    name = "list_time_slots"
    description = "List reservation time slots configuration."
    module_id = "reservations"
    required_permission = "reservations.view_reservation"
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from reservations.models import TimeSlot
        slots = TimeSlot.objects.filter(is_active=True).order_by('day_of_week', 'start_time')
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return {
            "slots": [
                {
                    "id": str(s.id),
                    "day": days[s.day_of_week],
                    "day_of_week": s.day_of_week,
                    "start_time": str(s.start_time),
                    "end_time": str(s.end_time),
                    "max_reservations": s.max_reservations,
                }
                for s in slots
            ]
        }


@register_tool
class CreateTimeSlot(AssistantTool):
    name = "create_time_slot"
    description = "Create a reservation time slot for a day of the week."
    module_id = "reservations"
    required_permission = "reservations.manage_settings"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "day_of_week": {"type": "integer", "description": "Day: 0=Monday to 6=Sunday"},
            "start_time": {"type": "string", "description": "Start time (HH:MM)"},
            "end_time": {"type": "string", "description": "End time (HH:MM)"},
            "max_reservations": {"type": "integer", "description": "Max simultaneous reservations"},
        },
        "required": ["day_of_week", "start_time", "end_time", "max_reservations"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from reservations.models import TimeSlot
        s = TimeSlot.objects.create(
            day_of_week=args['day_of_week'],
            start_time=args['start_time'],
            end_time=args['end_time'],
            max_reservations=args['max_reservations'],
        )
        return {"id": str(s.id), "created": True}


@register_tool
class CreateBlockedDate(AssistantTool):
    name = "create_blocked_date"
    description = "Block a date for reservations (e.g., holidays, private events)."
    module_id = "reservations"
    required_permission = "reservations.manage_settings"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "Date to block (YYYY-MM-DD)"},
            "reason": {"type": "string", "description": "Reason for blocking"},
            "is_full_day": {"type": "boolean", "description": "Block entire day (default true)"},
        },
        "required": ["date", "reason"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from reservations.models import BlockedDate
        b = BlockedDate.objects.create(
            date=args['date'],
            reason=args['reason'],
            is_full_day=args.get('is_full_day', True),
        )
        return {"id": str(b.id), "date": str(b.date), "created": True}


@register_tool
class GetReservationSettings(AssistantTool):
    name = "get_reservation_settings"
    description = "Get reservation settings (slot duration, party size limits, advance booking, auto-confirm)."
    module_id = "reservations"
    required_permission = "reservations.view_reservation"
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from reservations.models import ReservationSettings
        s = ReservationSettings.get_solo()
        return {
            "time_slot_duration": s.time_slot_duration,
            "min_party_size": s.min_party_size,
            "max_party_size": s.max_party_size,
            "min_advance_hours": s.min_advance_hours,
            "max_advance_days": s.max_advance_days,
            "auto_confirm": s.auto_confirm,
            "no_show_window_minutes": s.no_show_window_minutes,
            "default_duration_minutes": s.default_duration_minutes,
        }


@register_tool
class UpdateReservationSettings(AssistantTool):
    name = "update_reservation_settings"
    description = "Update reservation settings."
    module_id = "reservations"
    required_permission = "reservations.manage_settings"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "time_slot_duration": {"type": "integer"},
            "min_party_size": {"type": "integer"},
            "max_party_size": {"type": "integer"},
            "min_advance_hours": {"type": "integer"},
            "max_advance_days": {"type": "integer"},
            "auto_confirm": {"type": "boolean"},
            "no_show_window_minutes": {"type": "integer"},
            "default_duration_minutes": {"type": "integer"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from reservations.models import ReservationSettings
        s = ReservationSettings.get_solo()
        updated = []
        for field in ['time_slot_duration', 'min_party_size', 'max_party_size',
                       'min_advance_hours', 'max_advance_days', 'auto_confirm',
                       'no_show_window_minutes', 'default_duration_minutes']:
            if field in args:
                setattr(s, field, args[field])
                updated.append(field)
        if updated:
            s.save()
        return {"updated_fields": updated, "success": True}
