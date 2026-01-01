"""Reservations URL configuration."""

from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    # Main views
    path('', views.index, name='index'),
    path('calendar/', views.calendar, name='calendar'),
    path('list/', views.reservation_list, name='list'),
    path('waitlist/', views.waitlist, name='waitlist'),
    path('blocked/', views.blocked_dates, name='blocked_dates'),
    path('slots/', views.time_slots, name='time_slots'),

    # Reservation CRUD
    path('new/', views.reservation_create, name='create'),
    path('<int:reservation_id>/', views.reservation_detail, name='detail'),
    path('<int:reservation_id>/edit/', views.reservation_edit, name='edit'),

    # API - Reservation lifecycle
    path('api/create/', views.api_create_reservation, name='api_create'),
    path('api/update/', views.api_update_reservation, name='api_update'),
    path('api/confirm/', views.api_confirm_reservation, name='api_confirm'),
    path('api/seat/', views.api_seat_reservation, name='api_seat'),
    path('api/complete/', views.api_complete_reservation, name='api_complete'),
    path('api/cancel/', views.api_cancel_reservation, name='api_cancel'),
    path('api/no-show/', views.api_no_show_reservation, name='api_no_show'),

    # API - Query
    path('api/for-date/', views.api_reservations_for_date, name='api_for_date'),
    path('api/check-availability/', views.api_check_availability, name='api_check_availability'),

    # API - Waitlist
    path('api/waitlist/add/', views.api_add_to_waitlist, name='api_waitlist_add'),
    path('api/waitlist/convert/', views.api_convert_waitlist, name='api_waitlist_convert'),

    # API - Blocked dates
    path('api/block/', views.api_block_date, name='api_block'),
    path('api/unblock/', views.api_unblock_date, name='api_unblock'),

    # Settings
    path('settings/', views.reservations_settings, name='settings'),
    path('settings/save/', views.reservations_settings_save, name='settings_save'),
    path('settings/toggle/', views.reservations_settings_toggle, name='settings_toggle'),
    path('settings/input/', views.reservations_settings_input, name='settings_input'),
    path('settings/reset/', views.reservations_settings_reset, name='settings_reset'),
]
