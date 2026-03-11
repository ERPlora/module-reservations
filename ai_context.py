"""
AI context for the Reservations module.
Loaded into the assistant system prompt when this module's tools are active.
"""

CONTEXT = """
## Module Knowledge: Reservations

### Models
**Reservation** — A booking for a specific date/time/table.
- `guest_name`, `guest_phone`, `guest_email`
- `customer` → customers.Customer (optional FK — link to existing customer)
- `date` (DateField), `time` (TimeField)
- `party_size` (number of guests), `duration_minutes` (default 120)
- `table` → tables.Table (optional, can be assigned later)
- `status`: pending | confirmed | seated | completed | cancelled | no_show
- `notes` (guest requests), `internal_notes` (staff only)
- Timestamps: `confirmed_at`, `seated_at`, `completed_at`, `cancelled_at`
- `cancellation_reason`

**Status flow**:
pending → confirmed → seated → completed
pending/confirmed → cancelled
pending/confirmed → no_show

**TimeSlot** — Available booking windows per day of week.
- `day_of_week` (0=Monday … 6=Sunday)
- `start_time`, `end_time`
- `max_reservations`: capacity per slot
- `is_active`

**BlockedDate** — Dates/times when reservations are not allowed.
- `date`, `reason`
- `is_full_day`: True = whole day blocked
- `blocked_from`, `blocked_until`: for partial-day blocks

**WaitlistEntry** — Waiting list when slot is full.
- `guest_name`, `guest_phone`, `date`, `preferred_time`, `party_size`
- `customer` → Customer (optional)
- `is_contacted`, `is_converted`
- `reservation` → Reservation (FK, set when converted)
- `convert_to_reservation()`: creates Reservation and marks entry converted

### Key flows
1. Create reservation → status=pending
2. Staff confirms: reservation.confirm() → status=confirmed, confirmed_at=now
3. Guest arrives: reservation.seat(table) → status=seated, table assigned, table.status=reserved→occupied
4. Meal ends: reservation.complete() → status=completed
5. No-show: reservation.mark_no_show() → status=no_show
6. Cancel: reservation.cancel(reason) → status=cancelled

### Settings (ReservationSettings)
- `auto_confirm`: skip pending → confirmed automatically
- `min_advance_hours` (default 1), `max_advance_days` (default 30)
- `no_show_window_minutes` (default 15): auto no-show after this delay
- `default_duration_minutes` (default 120)
- `require_phone` (default True), `require_email` (default False)
- `send_confirmation_email`, `send_reminder_email`, `reminder_hours_before`

### Relationships
- Reservation → tables.Table (assigned table)
- Reservation → customers.Customer (optional link)
- WaitlistEntry → Reservation (when converted)
"""
