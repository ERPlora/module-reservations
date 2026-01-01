"""Reservations signal handlers."""

from django.dispatch import receiver
from apps.core.signals import table_closed


@receiver(table_closed)
def handle_table_closed(sender, table, duration_minutes, sale, **kwargs):
    """
    When a table is closed, check if there's a seated reservation
    and mark it as completed.
    """
    from .models import Reservation

    # Find seated reservation for this table
    reservation = Reservation.objects.filter(
        table_id=table.id,
        status=Reservation.STATUS_SEATED
    ).first()

    if reservation:
        reservation.complete()
