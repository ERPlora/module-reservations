from django.utils.translation import gettext_lazy as _

MODULE_ID = 'reservations'
MODULE_NAME = _('Reservations')
MODULE_VERSION = '2.0.7'

MENU = {
    'label': _('Reservations'),
    'icon': 'calendar-outline',
    'order': 26,
}

NAVIGATION = [
    {'id': 'today', 'label': _('Today'), 'icon': 'today-outline', 'view': ''},
    {'id': 'calendar', 'label': _('Calendar'), 'icon': 'calendar-outline', 'view': 'calendar'},
    {'id': 'list', 'label': _('List'), 'icon': 'list-outline', 'view': 'list'},
    {'id': 'waitlist', 'label': _('Waitlist'), 'icon': 'people-outline', 'view': 'waitlist'},
    {'id': 'availability', 'label': _('Availability'), 'icon': 'time-outline', 'view': 'availability'},
    {'id': 'settings', 'label': _('Settings'), 'icon': 'settings-outline', 'view': 'settings'},
]

PERMISSIONS = [
    'reservations.view_reservation',
    'reservations.add_reservation',
    'reservations.change_reservation',
    'reservations.delete_reservation',
    'reservations.view_timeslot',
    'reservations.change_timeslot',
    'reservations.view_blockeddate',
    'reservations.change_blockeddate',
    'reservations.view_waitlistentry',
    'reservations.change_waitlistentry',
    'reservations.view_reservationsettings',
    'reservations.change_reservationsettings',

    'reservations.manage_settings',
]

DEPENDENCIES = ['tables', 'customers']

ROLE_PERMISSIONS = {
    "admin": ["*"],
    "manager": [
        "add_reservation",
        "change_blockeddate",
        "change_reservation",
        "change_reservationsettings",
        "change_timeslot",
        "change_waitlistentry",
        "view_blockeddate",
        "view_reservation",
        "view_reservationsettings",
        "view_timeslot",
        "view_waitlistentry",
    ],
    "employee": [
        "add_reservation",
        "view_blockeddate",
        "view_reservation",
        "view_reservationsettings",
        "view_timeslot",
        "view_waitlistentry",
    ],
}
