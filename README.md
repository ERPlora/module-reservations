# Reservations

## Overview

| Property | Value |
|----------|-------|
| **Module ID** | `reservations` |
| **Version** | `2.0.0` |
| **Dependencies** | `tables`, `customers` |

## Dependencies

This module requires the following modules to be installed:

- `tables`
- `customers`

## Models

### `ReservationSettings`

Per-hub reservation settings.

| Field | Type | Details |
|-------|------|---------|
| `time_slot_duration` | PositiveIntegerField |  |
| `min_party_size` | PositiveIntegerField |  |
| `max_party_size` | PositiveIntegerField |  |
| `min_advance_hours` | PositiveIntegerField |  |
| `max_advance_days` | PositiveIntegerField |  |
| `auto_confirm` | BooleanField |  |
| `require_phone` | BooleanField |  |
| `require_email` | BooleanField |  |
| `no_show_window_minutes` | PositiveIntegerField |  |
| `default_duration_minutes` | PositiveIntegerField |  |
| `send_confirmation_email` | BooleanField |  |
| `send_reminder_email` | BooleanField |  |
| `reminder_hours_before` | PositiveIntegerField |  |

**Methods:**

- `get_settings()`

### `TimeSlot`

Available time windows per day of week.

| Field | Type | Details |
|-------|------|---------|
| `day_of_week` | IntegerField | choices: 0, 1, 2, 3, 4, 5, ... |
| `start_time` | TimeField |  |
| `end_time` | TimeField |  |
| `max_reservations` | PositiveIntegerField |  |
| `is_active` | BooleanField |  |

**Methods:**

- `get_slots_for_day()`

### `BlockedDate`

Dates when reservations are not allowed (holidays, closures, etc.).

| Field | Type | Details |
|-------|------|---------|
| `date` | DateField |  |
| `reason` | CharField | max_length=200, optional |
| `is_full_day` | BooleanField |  |
| `blocked_from` | TimeField | optional |
| `blocked_until` | TimeField | optional |

**Methods:**

- `is_blocked()` — Check if a date/time is blocked for a hub.

### `Reservation`

Individual reservation record.

| Field | Type | Details |
|-------|------|---------|
| `customer` | ForeignKey | → `customers.Customer`, on_delete=SET_NULL, optional |
| `guest_name` | CharField | max_length=200 |
| `guest_phone` | CharField | max_length=50, optional |
| `guest_email` | EmailField | max_length=254, optional |
| `date` | DateField |  |
| `time` | TimeField |  |
| `party_size` | PositiveIntegerField |  |
| `duration_minutes` | PositiveIntegerField |  |
| `table` | ForeignKey | → `tables.Table`, on_delete=SET_NULL, optional |
| `status` | CharField | max_length=20, choices: pending, confirmed, seated, completed, cancelled, no_show |
| `notes` | TextField | optional |
| `internal_notes` | TextField | optional |
| `confirmed_at` | DateTimeField | optional |
| `seated_at` | DateTimeField | optional |
| `completed_at` | DateTimeField | optional |
| `cancelled_at` | DateTimeField | optional |
| `cancellation_reason` | TextField | optional |

**Methods:**

- `confirm()`
- `seat()`
- `complete()`
- `cancel()`
- `mark_no_show()`
- `get_for_date()`
- `get_upcoming()`

**Properties:**

- `datetime`
- `end_datetime`
- `is_past`
- `is_today`
- `minutes_until`
- `is_upcoming`
- `table_display`
- `status_class`
- `can_be_confirmed`
- `can_be_seated`
- `can_be_completed`
- `can_be_cancelled`

### `WaitlistEntry`

Waitlist for fully booked time slots.

| Field | Type | Details |
|-------|------|---------|
| `guest_name` | CharField | max_length=200 |
| `guest_phone` | CharField | max_length=50 |
| `guest_email` | EmailField | max_length=254, optional |
| `customer` | ForeignKey | → `customers.Customer`, on_delete=SET_NULL, optional |
| `date` | DateField |  |
| `preferred_time` | TimeField |  |
| `party_size` | PositiveIntegerField |  |
| `notes` | TextField | optional |
| `is_contacted` | BooleanField |  |
| `is_converted` | BooleanField |  |
| `reservation` | ForeignKey | → `reservations.Reservation`, on_delete=SET_NULL, optional |

**Methods:**

- `convert_to_reservation()` — Convert waitlist entry to a reservation.

## Cross-Module Relationships

| From | Field | To | on_delete | Nullable |
|------|-------|----|-----------|----------|
| `Reservation` | `customer` | `customers.Customer` | SET_NULL | Yes |
| `Reservation` | `table` | `tables.Table` | SET_NULL | Yes |
| `WaitlistEntry` | `customer` | `customers.Customer` | SET_NULL | Yes |
| `WaitlistEntry` | `reservation` | `reservations.Reservation` | SET_NULL | Yes |

## URL Endpoints

Base path: `/m/reservations/`

| Path | Name | Method |
|------|------|--------|
| `(root)` | `index` | GET |
| `today/` | `today` | GET |
| `calendar/` | `calendar` | GET |
| `list/` | `list` | GET |
| `new/` | `create` | GET/POST |
| `<uuid:pk>/` | `detail` | GET |
| `<uuid:pk>/edit/` | `edit` | GET |
| `<uuid:pk>/delete/` | `delete` | GET/POST |
| `<uuid:pk>/confirm/` | `confirm` | GET |
| `<uuid:pk>/seat/` | `seat` | GET |
| `<uuid:pk>/complete/` | `complete` | GET |
| `<uuid:pk>/cancel/` | `cancel` | GET |
| `<uuid:pk>/no-show/` | `no_show` | GET |
| `waitlist/` | `waitlist` | GET |
| `waitlist/add/` | `waitlist_add` | GET/POST |
| `waitlist/<uuid:pk>/convert/` | `waitlist_convert` | GET |
| `waitlist/<uuid:pk>/delete/` | `waitlist_delete` | GET/POST |
| `availability/` | `availability` | GET |
| `timeslots/add/` | `timeslot_add` | GET/POST |
| `timeslots/<uuid:pk>/edit/` | `timeslot_edit` | GET |
| `timeslots/<uuid:pk>/delete/` | `timeslot_delete` | GET/POST |
| `blocked/add/` | `blocked_date_add` | GET/POST |
| `blocked/<uuid:pk>/delete/` | `blocked_date_delete` | GET/POST |
| `api/for-date/` | `api_for_date` | GET |
| `api/check-availability/` | `api_check_availability` | GET |
| `settings/` | `settings` | GET |
| `settings/save/` | `settings_save` | GET/POST |
| `settings/toggle/` | `settings_toggle` | GET |
| `settings/input/` | `settings_input` | GET |
| `settings/reset/` | `settings_reset` | GET |

## Permissions

| Permission | Description |
|------------|-------------|
| `reservations.view_reservation` | View Reservation |
| `reservations.add_reservation` | Add Reservation |
| `reservations.change_reservation` | Change Reservation |
| `reservations.delete_reservation` | Delete Reservation |
| `reservations.view_timeslot` | View Timeslot |
| `reservations.change_timeslot` | Change Timeslot |
| `reservations.view_blockeddate` | View Blockeddate |
| `reservations.change_blockeddate` | Change Blockeddate |
| `reservations.view_waitlistentry` | View Waitlistentry |
| `reservations.change_waitlistentry` | Change Waitlistentry |
| `reservations.view_reservationsettings` | View Reservationsettings |
| `reservations.change_reservationsettings` | Change Reservationsettings |
| `reservations.manage_settings` | Manage Settings |

**Role assignments:**

- **admin**: All permissions
- **manager**: `add_reservation`, `change_blockeddate`, `change_reservation`, `change_reservationsettings`, `change_timeslot`, `change_waitlistentry`, `view_blockeddate`, `view_reservation` (+3 more)
- **employee**: `add_reservation`, `view_blockeddate`, `view_reservation`, `view_reservationsettings`, `view_timeslot`, `view_waitlistentry`

## Navigation

| View | Icon | ID | Fullpage |
|------|------|----|----------|
| Today | `today-outline` | `today` | No |
| Calendar | `calendar-outline` | `calendar` | No |
| List | `list-outline` | `list` | No |
| Waitlist | `people-outline` | `waitlist` | No |
| Availability | `time-outline` | `availability` | No |
| Settings | `settings-outline` | `settings` | No |

## AI Tools

Tools available for the AI assistant:

### `list_reservations`

List reservations with filters. Returns guest, date, time, party size, status, table.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter: pending, confirmed, seated, completed, cancelled, no_show |
| `date` | string | No | Filter by date (YYYY-MM-DD) |
| `limit` | integer | No | Max results (default 20) |

### `create_reservation`

Create a new reservation.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `guest_name` | string | Yes | Guest name |
| `guest_phone` | string | No | Guest phone |
| `guest_email` | string | No | Guest email |
| `date` | string | Yes | Date (YYYY-MM-DD) |
| `time` | string | Yes | Time (HH:MM) |
| `party_size` | integer | Yes | Number of guests |
| `duration_minutes` | integer | No | Duration in minutes |
| `table_id` | string | No | Table ID |
| `notes` | string | No | Notes |

### `update_reservation_status`

Update reservation status: confirm, seat, complete, cancel, no_show.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `reservation_id` | string | Yes | Reservation ID |
| `status` | string | Yes | New status: confirmed, seated, completed, cancelled, no_show |
| `cancellation_reason` | string | No | Reason for cancellation |

### `list_time_slots`

List reservation time slots configuration.

### `create_time_slot`

Create a reservation time slot for a day of the week.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `day_of_week` | integer | Yes | Day: 0=Monday to 6=Sunday |
| `start_time` | string | Yes | Start time (HH:MM) |
| `end_time` | string | Yes | End time (HH:MM) |
| `max_reservations` | integer | Yes | Max simultaneous reservations |

### `create_blocked_date`

Block a date for reservations (e.g., holidays, private events).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date` | string | Yes | Date to block (YYYY-MM-DD) |
| `reason` | string | Yes | Reason for blocking |
| `is_full_day` | boolean | No | Block entire day (default true) |

### `get_reservation_settings`

Get reservation settings (slot duration, party size limits, advance booking, auto-confirm).

### `update_reservation_settings`

Update reservation settings.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `time_slot_duration` | integer | No |  |
| `min_party_size` | integer | No |  |
| `max_party_size` | integer | No |  |
| `min_advance_hours` | integer | No |  |
| `max_advance_days` | integer | No |  |
| `auto_confirm` | boolean | No |  |
| `no_show_window_minutes` | integer | No |  |
| `default_duration_minutes` | integer | No |  |

## File Structure

```
README.md
__init__.py
ai_tools.py
apps.py
forms.py
migrations/
  0001_initial.py
  0002_unique_together_to_constraints.py
  __init__.py
models.py
module.py
static/
  icons/
    ion/
templates/
  reservations/
    pages/
      availability.html
      calendar.html
      detail.html
      form.html
      index.html
      list.html
      settings.html
      today.html
      waitlist.html
    partials/
      availability.html
      calendar.html
      detail.html
      form.html
      list.html
      settings.html
      today.html
      waitlist.html
tests/
  __init__.py
  conftest.py
  test_models.py
  test_views.py
urls.py
views.py
```
