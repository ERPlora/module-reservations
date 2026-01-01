"""Reservations module definition."""


def get_module_info():
    """Return module metadata."""
    return {
        'module_id': 'reservations',
        'name': 'Reservations',
        'version': '1.0.0',
        'description': 'Restaurant reservation and booking management',
        'category': 'restaurant',
        'dependencies': [],
        'optional_dependencies': ['tables', 'customers'],
    }


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
