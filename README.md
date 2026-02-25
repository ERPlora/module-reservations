# Reservations Module

> **Note**: This module is currently disabled.

Table reservation management with time slots, availability control, waitlist, and guest tracking.

## Features

- Today view with upcoming and active reservations
- Calendar view for browsing reservations by date
- Full reservation list with filtering
- Waitlist management for fully booked time slots with conversion to reservation
- Availability configuration with time slots per day of week
- Blocked dates for holidays and closures (full-day or partial)
- Reservation lifecycle: pending, confirmed, seated, completed, cancelled, no-show
- Guest information with optional customer linking
- Table assignment from the tables module
- Party size and duration tracking
- Auto-confirm option for reservations
- Configurable advance booking limits (minimum hours, maximum days)
- No-show detection window
- Email confirmation and reminder settings
- Internal and guest-facing notes

## Installation

This module is installed automatically via the ERPlora Marketplace.

**Dependencies**: Requires `tables` and `customers` modules.

## Configuration

Access settings via: **Menu > Reservations > Settings**

Configurable options include:

- **Time slots**: Slot duration, min/max party size
- **Advance booking**: Minimum hours and maximum days in advance
- **Confirmation**: Auto-confirm, require phone/email
- **No-show**: Window in minutes after reservation time
- **Duration**: Default reservation duration
- **Notifications**: Confirmation and reminder emails with configurable timing

## Usage

Access via: **Menu > Reservations**

### Views

| View | URL | Description |
|------|-----|-------------|
| Today | `/m/reservations/today/` | View and manage today's reservations |
| Calendar | `/m/reservations/calendar/` | Browse reservations on a calendar view |
| List | `/m/reservations/list/` | Full list of all reservations with filters |
| Waitlist | `/m/reservations/waitlist/` | Manage waitlist entries for fully booked slots |
| Availability | `/m/reservations/availability/` | Configure time slots and blocked dates |
| Settings | `/m/reservations/settings/` | Configure reservation module settings |

## Models

| Model | Description |
|-------|-------------|
| `ReservationSettings` | Per-hub configuration for time slots, booking limits, confirmation rules, no-show handling, and notifications (singleton per hub) |
| `TimeSlot` | Available time windows per day of week with max reservation capacity and active status |
| `BlockedDate` | Dates or time ranges when reservations are not allowed (holidays, closures) |
| `Reservation` | Individual reservation with guest info, date/time, party size, table assignment, status lifecycle, and timestamps |
| `WaitlistEntry` | Waitlist entry for fully booked slots with guest info, preferred time, and conversion tracking |

## Permissions

| Permission | Description |
|------------|-------------|
| `reservations.view_reservation` | View reservations |
| `reservations.add_reservation` | Create new reservations |
| `reservations.change_reservation` | Edit existing reservations |
| `reservations.delete_reservation` | Delete reservations |
| `reservations.view_timeslot` | View time slot configuration |
| `reservations.change_timeslot` | Modify time slot configuration |
| `reservations.view_blockeddate` | View blocked dates |
| `reservations.change_blockeddate` | Modify blocked dates |
| `reservations.view_waitlistentry` | View waitlist entries |
| `reservations.change_waitlistentry` | Modify waitlist entries |
| `reservations.view_reservationsettings` | View reservation settings |
| `reservations.change_reservationsettings` | Modify reservation settings |

## Integration with Other Modules

- **tables**: Reservations can be assigned to tables from the tables module. The `Reservation.table` field references `tables.Table`.
- **customers**: Guests can be linked to existing customer records. The `Reservation.customer` and `WaitlistEntry.customer` fields reference `customers.Customer`.

## License

MIT

## Author

ERPlora Team - support@erplora.com
