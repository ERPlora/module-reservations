"""Reservations URL Configuration."""

from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    # Setup (initial configuration)
    path('setup/', views.setup, name='setup'),

    # Main views
    path('', views.index, name='index'),
    path('today/', views.today, name='today'),
    path('calendar/', views.calendar, name='calendar'),
    path('list/', views.reservation_list, name='list'),

    # Reservation CRUD
    path('new/', views.reservation_create, name='create'),
    path('<uuid:pk>/', views.reservation_detail, name='detail'),
    path('<uuid:pk>/edit/', views.reservation_edit, name='edit'),
    path('<uuid:pk>/delete/', views.reservation_delete, name='delete'),

    # Status actions
    path('<uuid:pk>/confirm/', views.confirm_reservation, name='confirm'),
    path('<uuid:pk>/seat/', views.seat_reservation, name='seat'),
    path('<uuid:pk>/complete/', views.complete_reservation, name='complete'),
    path('<uuid:pk>/cancel/', views.cancel_reservation, name='cancel'),
    path('<uuid:pk>/no-show/', views.no_show_reservation, name='no_show'),

    # Waitlist
    path('waitlist/', views.waitlist, name='waitlist'),
    path('waitlist/add/', views.waitlist_add, name='waitlist_add'),
    path('waitlist/<uuid:pk>/convert/', views.waitlist_convert, name='waitlist_convert'),
    path('waitlist/<uuid:pk>/delete/', views.waitlist_delete, name='waitlist_delete'),

    # Availability (time slots + blocked dates)
    path('availability/', views.availability, name='availability'),
    path('timeslots/add/', views.timeslot_add, name='timeslot_add'),
    path('timeslots/<uuid:pk>/edit/', views.timeslot_edit, name='timeslot_edit'),
    path('timeslots/<uuid:pk>/delete/', views.timeslot_delete, name='timeslot_delete'),
    path('blocked/add/', views.blocked_date_add, name='blocked_date_add'),
    path('blocked/<uuid:pk>/delete/', views.blocked_date_delete, name='blocked_date_delete'),

    # API
    path('api/for-date/', views.api_reservations_for_date, name='api_for_date'),
    path('api/check-availability/', views.api_check_availability, name='api_check_availability'),

    # Settings
    path('settings/', views.settings, name='settings'),
    path('settings/save/', views.settings_save, name='settings_save'),
    path('settings/toggle/', views.settings_toggle, name='settings_toggle'),
    path('settings/input/', views.settings_input, name='settings_input'),
    path('settings/reset/', views.settings_reset, name='settings_reset'),
]
