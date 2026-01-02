"""
Reservations Module Configuration

This file defines the module metadata and navigation for the Reservations module.
Restaurant reservation and booking management for hospitality businesses.
Used by the @module_view decorator to automatically render navigation tabs.
"""
from django.utils.translation import gettext_lazy as _

# Module Identification
MODULE_ID = "reservations"
MODULE_NAME = _("Reservations")
MODULE_ICON = "calendar-number-outline"
MODULE_VERSION = "1.0.0"
MODULE_CATEGORY = "horeca"  # Changed from "restaurant" to valid category

# Target Industries (business verticals this module is designed for)
MODULE_INDUSTRIES = [
    "restaurant", # Restaurants
    "bar",        # Bars & pubs
    "hotel",      # Hotels & lodging
    "catering",   # Catering & events
]

# Sidebar Menu Configuration
MENU = {
    "label": _("Reservations"),
    "icon": "calendar-number-outline",
    "order": 55,
    "show": True,
}

# Internal Navigation (Tabs)
NAVIGATION = [
    {
        "id": "dashboard",
        "label": _("Overview"),
        "icon": "grid-outline",
        "view": "",
    },
    {
        "id": "calendar",
        "label": _("Calendar"),
        "icon": "calendar-outline",
        "view": "calendar",
    },
    {
        "id": "list",
        "label": _("List"),
        "icon": "list-outline",
        "view": "list",
    },
    {
        "id": "settings",
        "label": _("Settings"),
        "icon": "settings-outline",
        "view": "settings",
    },
]

# Module Dependencies
DEPENDENCIES = []

# Optional Dependencies
OPTIONAL_DEPENDENCIES = ["tables", "customers"]

# Default Settings
SETTINGS = {
    "default_duration_minutes": 90,
    "max_party_size": 20,
    "min_advance_hours": 1,
    "max_advance_days": 90,
    "require_phone": True,
    "send_confirmations": True,
}

# Permissions
PERMISSIONS = [
    "reservations.view_reservation",
    "reservations.add_reservation",
    "reservations.change_reservation",
    "reservations.delete_reservation",
    "reservations.confirm_reservation",
    "reservations.cancel_reservation",
]


def on_install():
    """Called when module is installed."""
    from .models import ReservationsConfig
    ReservationsConfig.get_config()


def on_uninstall():
    """Called when module is uninstalled."""
    pass


def register_slots():
    """Register slots for other modules."""
    pass


def register_signals():
    """Register signal handlers."""
    from . import signals  # noqa: F401
