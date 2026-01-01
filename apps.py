"""Reservations app configuration."""

from django.apps import AppConfig


class ReservationsConfig(AppConfig):
    """Configuration for Reservations module."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reservations'
    verbose_name = 'Reservations'

    def ready(self):
        """Import signals when app is ready."""
        from . import signals  # noqa: F401
