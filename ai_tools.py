"""AI tools for the Reservations module."""
from assistant.tools import AssistantTool, register_tool


@register_tool
class ListReservations(AssistantTool):
    name = "list_reservations"
    description = (
        "Use this to browse or check reservations. "
        "Returns guest name, phone, date, time, party size, duration, status, assigned table, and notes. "
        "Results are ordered by date and time (earliest first). "
        "Read-only — no side effects. "
        "Example triggers: 'what reservations do we have today?', 'show confirmed reservations for Saturday', "
        "'check if there are pending bookings'"
    )
    module_id = "reservations"
    required_permission = "reservations.view_reservation"
    parameters = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": (
                    "Filter by reservation status. Options: "
                    "'pending' (awaiting confirmation), "
                    "'confirmed' (accepted), "
                    "'seated' (guests arrived and seated), "
                    "'completed' (visit finished), "
                    "'cancelled' (cancelled by guest or staff), "
                    "'no_show' (guest did not arrive). "
                    "Omit to return all statuses."
                ),
            },
            "date": {
                "type": "string",
                "description": "Filter reservations for a specific date in YYYY-MM-DD format.",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of reservations to return. Default is 20.",
            },
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
    description = (
        "Use this to book a new reservation for a guest. "
        "SIDE EFFECT: creates a new Reservation record (status starts as 'pending' unless auto_confirm is on). "
        "Requires confirmation. "
        "Guest name, date, time, and party size are required. "
        "Use list_time_slots to verify the slot is open and list_tables to assign a table. "
        "Use get_reservation_settings to check advance booking limits and default duration. "
        "Example triggers: 'book a table for 4 on Friday at 8pm', 'make a reservation for Carlos for tomorrow'"
    )
    module_id = "reservations"
    required_permission = "reservations.add_reservation"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "guest_name": {
                "type": "string",
                "description": "Full name of the guest making the reservation. Required.",
            },
            "guest_phone": {
                "type": "string",
                "description": "Guest's contact phone number.",
            },
            "guest_email": {
                "type": "string",
                "description": "Guest's email address.",
            },
            "date": {
                "type": "string",
                "description": "Reservation date in YYYY-MM-DD format. Required.",
            },
            "time": {
                "type": "string",
                "description": "Reservation time in HH:MM (24-hour) format. Required.",
            },
            "party_size": {
                "type": "integer",
                "description": "Number of guests in the party. Required. Must be within min/max configured in reservation settings.",
            },
            "duration_minutes": {
                "type": "integer",
                "description": "Expected duration in minutes. Defaults to the configured default_duration_minutes (typically 90).",
            },
            "table_id": {
                "type": "string",
                "description": "UUID of the pre-assigned table. Use list_tables to find available tables. Optional — can be assigned later.",
            },
            "notes": {
                "type": "string",
                "description": "Special requests or notes (e.g., 'Birthday cake', 'Allergy: shellfish', 'Window table preferred').",
            },
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
    description = (
        "Use this to advance or change the status of a reservation through its lifecycle. "
        "SIDE EFFECT: updates reservation status and timestamps. Requires confirmation. "
        "Status transitions: pending → confirmed → seated → completed. "
        "A reservation can also be cancelled (with a reason) or marked as no_show. "
        "Use list_reservations to find the reservation_id."
    )
    module_id = "reservations"
    required_permission = "reservations.change_reservation"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "reservation_id": {
                "type": "string",
                "description": "UUID of the reservation to update.",
            },
            "status": {
                "type": "string",
                "description": (
                    "New status. Options: "
                    "'confirmed' (accept the booking), "
                    "'seated' (guests have arrived and are at the table), "
                    "'completed' (visit finished), "
                    "'cancelled' (booking cancelled — provide cancellation_reason), "
                    "'no_show' (guests did not arrive)."
                ),
            },
            "cancellation_reason": {
                "type": "string",
                "description": "Reason for cancellation. Provide when status is 'cancelled'.",
            },
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
    description = (
        "Use this to see the configured reservation time slots for each day of the week. "
        "Returns day name, start time, end time, and maximum simultaneous reservations per slot. "
        "Read-only — no side effects. "
        "Call this before creating a reservation to verify the requested time falls within an active slot. "
        "Call this before create_time_slot to avoid duplicates."
    )
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
    description = (
        "Use this to define a reservation time window for a specific day of the week "
        "(e.g., Friday dinner service from 20:00 to 23:00, max 8 simultaneous bookings). "
        "SIDE EFFECT: creates a new TimeSlot record. Requires confirmation. "
        "Call list_time_slots first to check existing slots and avoid overlaps."
    )
    module_id = "reservations"
    required_permission = "reservations.manage_settings"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "day_of_week": {
                "type": "integer",
                "description": "Day of the week as an integer: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday.",
            },
            "start_time": {
                "type": "string",
                "description": "Slot opening time in HH:MM (24-hour) format (e.g., '13:00', '20:00').",
            },
            "end_time": {
                "type": "string",
                "description": "Slot closing time in HH:MM (24-hour) format (e.g., '15:30', '23:00').",
            },
            "max_reservations": {
                "type": "integer",
                "description": "Maximum number of reservations that can be booked simultaneously in this slot.",
            },
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
    description = (
        "Use this to block a specific date so no new reservations can be made on that day "
        "(e.g., public holidays, private events, staff days off). "
        "SIDE EFFECT: creates a BlockedDate record that prevents reservations on that date. Requires confirmation. "
        "Example triggers: 'block December 25th for holidays', 'close reservations on the 15th for a private event'"
    )
    module_id = "reservations"
    required_permission = "reservations.manage_settings"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "The date to block in YYYY-MM-DD format. Required.",
            },
            "reason": {
                "type": "string",
                "description": "Reason for blocking (e.g., 'Navidad', 'Evento privado', 'Cierre por obras'). Required.",
            },
            "is_full_day": {
                "type": "boolean",
                "description": "If true (default), the entire day is blocked. Set to false for partial-day blocks.",
            },
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
    description = (
        "Use this to read the current reservation module configuration. "
        "Returns: time_slot_duration (minutes), min/max party size, "
        "min_advance_hours (how far ahead guests must book), max_advance_days (how far in the future), "
        "auto_confirm (whether bookings are auto-confirmed), no_show_window_minutes, "
        "and default_duration_minutes. "
        "Read-only — no side effects. "
        "Call this before update_reservation_settings to see current values."
    )
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
    description = (
        "Use this to change the reservation module configuration. "
        "SIDE EFFECT: updates the global reservation settings. Requires confirmation. "
        "Only the fields you provide are updated; omitted fields remain unchanged. "
        "Key settings: auto_confirm=true skips manual confirmation step; "
        "max_party_size limits group sizes; min_advance_hours prevents last-minute bookings. "
        "Call get_reservation_settings first to see current values."
    )
    module_id = "reservations"
    required_permission = "reservations.manage_settings"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "time_slot_duration": {
                "type": "integer",
                "description": "Duration of each time slot in minutes (e.g., 30 or 60).",
            },
            "min_party_size": {
                "type": "integer",
                "description": "Minimum number of guests allowed per reservation.",
            },
            "max_party_size": {
                "type": "integer",
                "description": "Maximum number of guests allowed per reservation.",
            },
            "min_advance_hours": {
                "type": "integer",
                "description": "Minimum hours in advance a reservation must be made (e.g., 2 means at least 2 hours ahead).",
            },
            "max_advance_days": {
                "type": "integer",
                "description": "Maximum days in advance a reservation can be made (e.g., 30 means bookings up to 30 days out).",
            },
            "auto_confirm": {
                "type": "boolean",
                "description": "If true, reservations are automatically confirmed without manual review.",
            },
            "no_show_window_minutes": {
                "type": "integer",
                "description": "Minutes after the reservation time before a guest can be marked as no-show.",
            },
            "default_duration_minutes": {
                "type": "integer",
                "description": "Default visit duration in minutes used when creating reservations (e.g., 90).",
            },
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
