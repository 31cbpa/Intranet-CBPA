from django.urls import path
from web.views import *
from .health import *

urlpatterns = [
    # Health
    path('health/', health_check, name='health_check'),
    path('health/resolve-alert/<int:alert_id>/', resolve_alert, name='resolve_alert'),

    # Auth
    path('iniciar-sesion/', login_view, name='login'),
    path('cerrar-sesion/', logout_view, name='logout'),
    path('password_recovery/', password_recovery, name='password_recovery'),
    path('password_recovery/<recovery_code>/', password_reset, name='password_reset'),

    # Main
    path('', home, name='home'),

    # Users
    path('users/', list_users, name='list_users'),
    path('users/<int:id>/', detail_user, name='detail_user'),
    path('users/create/', create_user, name='create_user'),
    path('users/remove/<int:id>/', remove_user, name='remove_user'),

    # Companies
    path('companies/', list_companies, name='list_companies'),
    path('companies/<int:id>/', detail_company, name='detail_company'),
    path('companies/create/', create_company, name='create_company'),
    path('companies/remove/<int:id>/', remove_company, name='remove_company'),

    # Vehicles
    path('vehicles/', list_vehicles, name='list_vehicles'),
    path('vehicles/<int:id>/', detail_vehicle, name='detail_vehicle'),
    path('vehicles/create/', create_vehicle, name='create_vehicle'),
    path('vehicles/remove/<int:id>/', remove_vehicle, name='remove_vehicle'),

    # Repairs
    path('repairs/', list_repairs, name='list_repairs'),
    path('repairs/pending/', list_pending_repairs, name='list_pending_repairs'),
    path('repairs/approve/<int:id>/', approve_repair, name='approve_repair'),
    path('repairs/<int:id>/', detail_repair, name='detail_repair'),
    path('repairs/create/<int:vehicle_id>/', create_repair, name='create_repair'),
    path('repairs/remove/<int:id>/', remove_repair, name='remove_repair'),
    path('repairs/start/<int:id>/', start_repair, name='start_repair'),

    # Parts
    path('parts/', list_parts, name='list_parts'),
    path('parts/create/<int:repair_id>/', create_parts, name='create_parts'),
    path('parts/<int:id>/', detail_parts, name='detail_parts'),
    
    # Admin
    path('server/', server, name='server'),

    # Firefighters
    path('firefighters/', list_firefighters, name='list_firefighters'),
    path('firefighters/create/', create_firefighter, name='create_firefighter'),
    path('firefighters/<int:id>/', detail_firefighter, name='detail_firefighter'),
    path('firefighters/<int:id>/edit/', edit_firefighter, name='edit_firefighter'),
    path('firefighters/<int:id>/remove/', remove_firefighter, name='remove_firefighter'),

]