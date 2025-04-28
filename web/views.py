from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import UserProfile
from django.shortcuts import render, redirect
from web.decorators import role_required
from web.models import *
from django.contrib.auth.models import Group
from django.db.models import Sum
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta, datetime
import psutil
import platform
import socket
import random
from .forms import FirefighterForm, EmergencyContactFormSet
from django.db import transaction


# Auth
def login_view(request):

    if request.method == 'POST':
        email = request.POST['txtEmail']
        password = request.POST['txtPassword']

        user = authenticate(username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        
        else:
            return render(request, 'auth/login.html', {'error_message': 'Las credenciales no son válidas.'})
        

    return render(request, 'auth/login.html')

@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('login')

def password_recovery(request):
    if request.method == 'POST':
        email = request.POST.get('txtEmail')
        user_profile = UserProfile.objects.filter(user__email=email).first()

        if user_profile:
            user_code = get_random_string(length=20)
            user_profile.recovery_password_code = user_code
            user_profile.recovery_password_expiration = timezone.now() + timedelta(days=1)
            user_profile.save()
            return render(request, 'auth/password_recovery.html', {
                'successful_message': 'Si tu correo electrónico es correcto, te enviaremos un enlace para la recuperación de tu contraseña.'
            })
        else:
            return render(request, 'auth/password_recovery.html', {
                'error_message': 'No se encontró un usuario con ese correo electrónico.'
            })

    return render(request, 'auth/password_recovery.html')

def password_reset(request, recovery_code):

    user = UserProfile.objects.get(recovery_password_code=recovery_code)

    if timezone.now() > user.recovery_password_expiration:
            return render(request, 'auth/password_reset.html', {'error_message': 'El enlace de recuperación de contraseña no es válido o ya expiró, intenta nuevamente.'})

    if request.method == 'POST':
            new_password = request.POST.get('txtNewPassword')
            confirm_password = request.POST.get('txtConfirmPassword')
            if new_password == confirm_password:
                user.user.set_password(new_password)
                user.user.save()
                user.recovery_password_code = ''    
                user.recovery_password_expiration = None
                user.save()
                request.session['password_reset_successful'] = True
                return redirect('login')
            else:
                return render(request, 'auth/password_reset.html', {'error_message': 'Las contraseñas no coinciden.'})
 
    return render(request, 'auth/password_reset.html')
    



# Main
@login_required(login_url='login')
def home(request):

    # Redirections
    if request.user.groups.filter(name='Mecánico').exists():
        return redirect('list_repairs')


    # Counters
    companies_count = Company.objects.count()
    vehicles_count = Vehicle.objects.count()
    repairs_count = Repair.objects.count()
    parts_count = Part.objects.count()
    firefighters_count = Firefighter.objects.count()
    
    # Últimos registros
    last_repairs = Repair.objects.all()
    last_vehicles = Vehicle.objects.all().order_by('-id')[:5]
    last_firefighters = Firefighter.objects.all().order_by('-id')[:5]

    for vehicle in last_vehicles:
        vehicle.active_repairs_count = Repair.objects.filter(vehicle=vehicle, status='En progreso').count()

    total_cost = Part.objects.aggregate(Sum('value'))['value__sum']
    if total_cost == None:
        total_cost = 0


    context = {
        'companies_count': companies_count,
        'vehicles_count': vehicles_count,
        'repairs_count': repairs_count,
        'parts_count': parts_count,
        'firefighters_count': firefighters_count,
        'total_cost': total_cost,
        'last_repairs': last_repairs,
        'last_vehicles': last_vehicles,
        'last_firefighters': last_firefighters,
        'page_nav_title': 'Inicio'
    }
    return render(request, 'home.html', context)

# Users
@role_required(allowed_roles=['Administrador'])
@login_required(login_url='login')
def list_users(request):

    users = User.objects.all()

    context = {
        'users': users,
        'page_nav_title': 'Gestor de Usuarios'
    }
    return render(request, 'users/list.html', context)

@login_required(login_url='login')
def detail_user(request, id):

    user = User.objects.get(id=id)
    user_profile = UserProfile.objects.get(user=user)

    if request.method == 'POST':
        user.first_name = request.POST['txtFirstName']
        user.last_name = request.POST['txtLastName']
        user.email = request.POST['txtEmail']
        user.save()

        user_profile.role = request.POST['txtRole']
        user_profile.save()

        messages.success(request, '¡Usuario actualizado correctamente!', extra_tags='alert-success')
        return redirect('list_users')

    context = {
        'user': user,
        'user_profile': user_profile,
        'page_nav_title': 'Usuario #USR-' + str(user.id)
    }
    return render(request, 'users/detail.html', context)

@login_required(login_url='login')
def create_user(request):

    if request.method == 'POST':
        email = request.POST['txtEmail']
        password = request.POST['txtPassword']
        first_name = request.POST['txtFirstName']
        last_name = request.POST['txtLastName']
        role = request.POST['txtRole']

        user = User.objects.create_user(email, email, password)
        user.first_name = first_name
        user.last_name = last_name
        user.groups.add(Group.objects.get(id=role))
        user.save()

        messages.success(request, '¡Usuario creado correctamente!', extra_tags='alert-success')
        return redirect('list_users')
    
    groups = Group.objects.all()
    context = {
        'groups': groups,
        'page_nav_title': 'Registro de Usuario'
    }
    return render(request, 'users/create.html', context)

@login_required(login_url='login')
def remove_user(request, id):

    user = User.objects.get(id=id)
    user.delete()

    messages.success(request, '¡Usuario eliminado correctamente!', extra_tags='alert-success')
    return redirect('list_users')


# Companies
@role_required(allowed_roles=['Administrador', 'Superintendente', 'Comandante'])
@login_required(login_url='login')
def list_companies(request):

    companies = Company.objects.all()

    context = {
        'companies': companies,
        'user_role': UserProfile.objects.get(user=request.user).role,
        'page_nav_title': 'Gestor de Compañías'
    }
    return render(request, 'companies/list.html', context)

@login_required(login_url='login')
def detail_company(request, id):

    company = Company.objects.get(id=id)

    if request.method == 'POST':
        company.name = request.POST['txtCompanyName']
        company.address = request.POST['txtCompanyAddress']
        company.volunteers = request.POST['txtCompanyVolunteers']
        company.director = request.POST['txtCompanyDirector']
        company.contact = request.POST['txtCompanyContact']

        company.save()

        messages.success(request, '¡Compañia actualizada correctamente!', extra_tags='alert-success')
        return redirect('list_companies')

    context = {
        'company': company,
        'page_nav_title': 'Compañía #COM-' + str(company.id)
    }
    return render(request, 'companies/detail.html', context)

@login_required(login_url='login')
def create_company(request):

    if request.method == 'POST':
        company_name = request.POST['txtCompanyName']
        company_address = request.POST['txtCompanyAddress']
        company_volunteers = request.POST['txtCompanyVolunteers']
        company_director = request.POST['txtCompanyDirector']
        company_contact = request.POST['txtCompanyContact']
        
        company_profile = Company(name=company_name, address=company_address, volunteers=company_volunteers, director=company_director, contact=company_contact)
        company_profile.save()

        messages.success(request, '¡Compañía creada correctamente!', extra_tags='alert-success')
        return redirect('list_companies')
    

    context = {
        'page_nav_title': 'Registro de Compañía'
    }
    return render(request, 'companies/create.html', context)

@login_required(login_url='login')
def remove_company(request, id):

    company = Company.objects.get(id=id)
    company.delete()

    messages.success(request, '¡Compañia eliminada correctamente!', extra_tags='alert-success')
    return redirect('list_companies')


# Vehicles
@login_required(login_url='login')
def list_vehicles(request):

    vehicles = Vehicle.objects.all()
    
    for vehicle in vehicles:
        vehicle.active_repairs_count = Repair.objects.filter(vehicle=vehicle, status='En progreso').count()

    context = {
        'vehicles': vehicles,
        'page_nav_title': 'Gestor de Vehículos'
    }
    return render(request, 'vehicles/list.html', context)

@login_required(login_url='login')
def detail_vehicle(request, id):

    vehicle = Vehicle.objects.get(id=id)
    repairs = Repair.objects.filter(vehicle=vehicle)

    if request.method == 'POST':

        company = Company.objects.get(id=request.POST['txtCompany'])

        vehicle.company = company
        vehicle.car_code = request.POST['txtCarCode']
        vehicle.car_type = request.POST['txtCarType']
        vehicle.license_plate = request.POST['txtLicensePlate']
        vehicle.brand = request.POST['txtBrand']
        vehicle.model = request.POST['txtModel']
        vehicle.year = int(request.POST['txtYear'])
        vehicle.technical_inspection = request.POST['txtTechnicalInspection']
        vehicle.emissions_inspection = request.POST['txtEmissionsInspection']
        vehicle.vehicle_registration = request.POST['txtVehicleRegistration']
        vehicle.insurance = request.POST['txtInsurance']
        vehicle.insurance_exp_date = request.POST['txtInsuranceExpDate']
        vehicle.save()

        messages.success(request, '¡Vehículo actualizado correctamente!', extra_tags='alert-success')
        return redirect('list_vehicles')

    companies = Company.objects.all()
    context = {
        'vehicle': vehicle,
        'companies': companies,
        'repairs': repairs,
        'page_nav_title': 'Vehículo #VEH-' + str(vehicle.id)
    }
    return render(request, 'vehicles/detail.html', context)

@login_required(login_url='login')
def create_vehicle(request):

    if request.method == 'POST':

        company = Company.objects.get(id=request.POST['txtCompany'])

        vehicle = Vehicle()
        vehicle.company = company
        vehicle.car_code = str(request.POST['txtCarCode']).upper()
        vehicle.car_type = request.POST.get('txtCarType', '').upper()
        vehicle.license_plate = str(request.POST['txtLicensePlate']).upper()
        vehicle.brand = str(request.POST['txtBrand']).title()
        vehicle.model = str(request.POST['txtModel']).title()
        vehicle.year = int(request.POST['txtYear'])
        vehicle.technical_inspection = request.POST['txtTechnicalInspection']
        vehicle.emissions_inspection = request.POST['txtEmissionsInspection']
        vehicle.vehicle_registration = request.POST['txtVehicleRegistration']
        vehicle.insurance = request.POST['txtInsurance']
        vehicle.insurance_exp_date = request.POST['txtInsuranceExpDate']
        vehicle.save()

        messages.success(request, '¡Vehículo creado correctamente!', extra_tags='alert-success')
        return redirect('list_vehicles')

    companies = Company.objects.all()
    context = {
        'companies': companies,
        'page_nav_title': 'Registro de Vehículo'
    }
    return render(request, 'vehicles/create.html', context)

@login_required(login_url='login')
def remove_vehicle(request, id):

    vehicle = Vehicle.objects.get(id=id)
    vehicle.delete()

    messages.success(request, '¡Vehículo eliminado correctamente!', extra_tags='alert-success')
    return redirect('list_vehicles')


# Repairs
@role_required(allowed_roles=['Administrador', 'Comandante', 'Mecánico'])
@login_required(login_url='login')
def list_repairs(request):

    if request.user.groups.filter(name='Mecánico').exists():
        repairs = Repair.objects.exclude(status='Pendiente')

    elif request.user.groups.filter(name='Comandante').exists():
        repairs = Repair.objects.filter(status='Pendiente')

    else:
        repairs = Repair.objects.all()

    context = {
        'repairs': repairs,
        'page_nav_title': 'Gestor de Reparaciones'
    }
    return render(request, 'repairs/list.html', context)

@role_required(allowed_roles=['Administrador', 'Comandante'])
@login_required(login_url='login')
def list_pending_repairs(request):

    repairs = Repair.objects.filter(status='Pendiente')

    context = {
        'repairs': repairs,
        'page_nav_title': 'Reparaciones Pendientes'
    }
    return render(request, 'repairs/pending-list.html', context)

@role_required(allowed_roles=['Administrador', 'Comandante'])
@login_required(login_url='login')
def approve_repair(request, id):

    repair = Repair.objects.get(id=id)
    repair.status = 'Sin comenzar'
    repair.save()

    messages.success(request, '¡Reparación aprobada correctamente! Ahora puede ser iniciada por un mecánico y trabajar en ella.', extra_tags='alert-success')
    return redirect('list_repairs')

@role_required(allowed_roles=['Administrador', 'Comandante', 'Mecánico'])
@login_required(login_url='login')
def detail_repair(request, id):

    repair = Repair.objects.get(id=id)
    vehicles = Vehicle.objects.all()
    companies = Company.objects.all()
    parts = Part.objects.filter(repair=repair)

    attachments = RepairAttachment.objects.filter(repair=repair)

    if request.method == 'POST':
        repair.title = request.POST['txtTitle']
        repair.resolution = request.POST['txtResolution']
        repair.save()

        messages.success(request, '¡Reparación actualizada correctamente!', extra_tags='alert-success')
        return redirect('list_repairs')

    context = {
        'repair': repair,
        'vehicles': vehicles,
        'companies': companies,
        'attachments': attachments,
        'parts': parts,
        'page_nav_title': 'Reparación #REP-' + str(repair.id)
    }
    return render(request, 'repairs/detail.html', context)

@login_required(login_url='login')
def create_repair(request, vehicle_id):

    vehicle = Vehicle.objects.get(id=vehicle_id)

    if request.method == 'POST':

        repair_name = request.POST['txtRepairName']
        repair_comments = request.POST['txtRepairComments']
        repair_attachments = request.FILES.getlist('fileAttachments')

        repair = Repair()
        repair.title = repair_name
        repair.status = 'Pendiente'
        repair.resolution = ''
        repair.vehicle = vehicle
        repair.comments = repair_comments
        repair.save()

        for attachment in repair_attachments:
            repair_attachment = RepairAttachment(repair=repair, attachment=attachment)
            repair_attachment.save()

        messages.success(request, '¡Solicitud de reparación creada correctamente!', extra_tags='alert-success')
        return redirect('detail_vehicle', id=vehicle.id)

    context = {
        'vehicle': vehicle,
        'page_nav_title': 'Solicitud de Reparación'
    }
    return render(request, 'repairs/create.html', context)

@login_required(login_url='login')
def remove_repair(request, id):

    repair = Repair.objects.get(id=id)
    repair.delete()

    messages.success(request, '¡Reparación eliminada correctamente!', extra_tags='alert-success')
    return redirect('list_repairs')

@role_required(allowed_roles=['Administrador', 'Mecánico'])
@login_required(login_url='login')
def start_repair(request, id):

    repair = Repair.objects.get(id=id)
    repair.status = 'En progreso'
    repair.save()

    messages.success(request, '¡Reparación iniciada correctamente! Ahora puede comenzar a trabajar en ella.', extra_tags='alert-success')
    return redirect('list_repairs')


# Parts
@login_required(login_url='login')
def list_parts(request):

    parts = Part.objects.all()

    context = {
        'parts': parts,
        'page_nav_title': 'Gestor de Compras de Repuestos'
    }
    return render(request, 'parts/list.html', context)

@login_required(login_url='login')
def create_parts(request, repair_id):

    repair = Repair.objects.get(id=repair_id)

    if request.method == 'POST':

        part_name = request.POST['txtPartsName']
        part_value = request.POST['txtPartsValue']
        part_attachments = request.FILES.getlist('partAttachments')

        part = Part()
        part.repair = repair
        part.name = part_name
        part.value = part_value
        part.save()

        for attachment in part_attachments:
            parts_attachment = PartAttachment(part=part, attachment=attachment)
            parts_attachment.save()

        messages.success(request, '¡Repuesto registrado correctamente!', extra_tags='alert-success')
        return redirect('detail_repair', id=repair.id)

    context = {
        'repair': repair,
        'page_nav_title': 'Registro de Compra de Repuesto'
    }
    return render(request, 'parts/create.html', context)

@login_required(login_url='login')
def detail_parts(request, id):

    part = Part.objects.get(id=id)
    attachments = PartAttachment.objects.filter(part=part)

    if request.method == 'POST':

        part_name = request.POST['txtPartsName']
        part_value = request.POST['txtPartsValue']

        part = Part()
        part.name = part_name
        part.value = part_value
        part.save()

    context = {
        'attachments': attachments,
        'part': part,
        'page_nav_title': 'Repuesto #PAR-' + str(part.id)
    }
    return render(request, 'parts/detail.html', context)

User = get_user_model()

@login_required(login_url='login')
def server(request):
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    
    # Calcular memoria disponible
    mem = psutil.virtual_memory()
    free_memory = round(mem.available / (1024 ** 3), 2)

    context = {
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname()),
        "platform": platform.platform(),
        "os": platform.system(),
        "os_version": platform.version(),
        "cpu_cores": psutil.cpu_count(logical=True),
        "cpu_usage": psutil.cpu_percent(interval=1),
        "total_memory": round(mem.total / (1024 ** 3), 2),
        "used_memory": round(mem.used / (1024 ** 3), 2),
        "free_memory": free_memory,  # Añadimos memoria disponible
        "memory_percent": mem.percent,
        "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
        "page_nav_title": "Administración del Servidor"  # Añadimos título para la barra de navegación
    }

    return render(request, "server/home.html", context)

# Bomberos
@role_required(allowed_roles=['Administrador', 'Superintendente', 'Secretario Comandancia', 'Secretario Compañía'])
@login_required(login_url='login')
def list_firefighters(request):
    user_groups = [group.name for group in request.user.groups.all()]
    
    # Determinar qué bomberos mostrar según el rol del usuario
    if any(role in user_groups for role in ['Administrador', 'Superintendente', 'Secretario Comandancia']):
        # Estos roles pueden ver todos los bomberos
        firefighters = Firefighter.objects.all()
    elif 'Secretario Compañía' in user_groups:
        # Secretarios de compañía solo ven bomberos de su compañía
        company = request.user.userprofile.company
        if company:
            firefighters = Firefighter.objects.filter(company=company)
        else:
            firefighters = Firefighter.objects.none()
    else:
        firefighters = Firefighter.objects.none()
    
    context = {
        'firefighters': firefighters,
        'can_edit': any(role in user_groups for role in ['Administrador', 'Secretario Comandancia', 'Secretario Compañía']),
        'page_nav_title': 'Gestor de Bomberos'
    }
    return render(request, 'firefighters/list.html', context)

@login_required(login_url='login')
def detail_firefighter(request, id):
    firefighter = Firefighter.objects.get(id=id)
    
    # Verificar permisos
    user_groups = [group.name for group in request.user.groups.all()]
    can_view = any(role in user_groups for role in ['Administrador', 'Superintendente', 'Secretario Comandancia'])
    
    if not can_view and 'Secretario Compañía' in user_groups:
        # Verificar si el secretario pertenece a la misma compañía
        company = request.user.userprofile.company
        if company and firefighter.company == company:
            can_view = True
    
    if not can_view:
        return redirect('home')
    
    emergency_contacts = firefighter.emergency_contacts.all()
    
    context = {
        'firefighter': firefighter,
        'emergency_contacts': emergency_contacts,
        'can_edit': any(role in user_groups for role in ['Administrador', 'Secretario Comandancia', 'Secretario Compañía']),
        'page_nav_title': 'Bombero #BOM-' + str(firefighter.id)
    }
    return render(request, 'firefighters/detail.html', context)

@role_required(allowed_roles=['Administrador', 'Secretario Comandancia', 'Secretario Compañía'])
@login_required(login_url='login')
@transaction.atomic
def create_firefighter(request):
    user_groups = [group.name for group in request.user.groups.all()]
    
    # Determinar compañías disponibles para el formulario
    if 'Secretario Compañía' in user_groups:
        # Secretarios de compañía solo pueden asignar a su compañía
        company = request.user.userprofile.company
        initial = {'company': company} if company else {}
        form = FirefighterForm(initial=initial)
        if company:
            form.fields['company'].queryset = Company.objects.filter(pk=company.pk)
            form.fields['company'].widget.attrs['readonly'] = True
    else:
        # Roles que pueden elegir cualquier compañía
        form = FirefighterForm()
    
    if request.method == 'POST':
        form = FirefighterForm(request.POST)
        formset = EmergencyContactFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            # Si es secretario, forzar la compañía
            if 'Secretario Compañía' in user_groups and request.user.userprofile.company:
                firefighter = form.save(commit=False)
                firefighter.company = request.user.userprofile.company
                firefighter.save()
            else:
                firefighter = form.save()
                
            # Guardar contactos de emergencia
            formset = EmergencyContactFormSet(request.POST, instance=firefighter)
            if formset.is_valid():
                formset.save()
                
            messages.success(request, '¡Bombero creado correctamente!', extra_tags='alert-success')
            return redirect('detail_firefighter', id=firefighter.id)
    else:
        formset = EmergencyContactFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Crear Bombero',
        'page_nav_title': 'Registro de Bombero'
    }
    return render(request, 'firefighters/form.html', context)

@role_required(allowed_roles=['Administrador', 'Secretario Comandancia', 'Secretario Compañía'])
@login_required(login_url='login')
@transaction.atomic
def edit_firefighter(request, id):
    firefighter = Firefighter.objects.get(id=id)
    user_groups = [group.name for group in request.user.groups.all()]
    
    # Verificar permisos de edición para secretarios de compañía
    if 'Secretario Compañía' in user_groups:
        company = request.user.userprofile.company
        if not company or firefighter.company != company:
            return redirect('home')
    
    if request.method == 'POST':
        form = FirefighterForm(request.POST, instance=firefighter)
        formset = EmergencyContactFormSet(request.POST, instance=firefighter)
        
        if form.is_valid() and formset.is_valid():
            # Preservar la compañía original si es secretario de compañía
            if 'Secretario Compañía' in user_groups:
                firefighter = form.save(commit=False)
                firefighter.company = request.user.userprofile.company
                firefighter.save()
            else:
                firefighter = form.save()
                
            formset.save()
            messages.success(request, '¡Bombero actualizado correctamente!', extra_tags='alert-success')
            return redirect('detail_firefighter', id=firefighter.id)
    else:
        form = FirefighterForm(instance=firefighter)
        formset = EmergencyContactFormSet(instance=firefighter)
        
        # Bloquear cambio de compañía para secretarios
        if 'Secretario Compañía' in user_groups:
            form.fields['company'].widget.attrs['readonly'] = True
            form.fields['company'].queryset = Company.objects.filter(pk=firefighter.company.pk)
    
    context = {
        'form': form,
        'formset': formset,
        'firefighter': firefighter,
        'title': 'Editar Bombero',
        'page_nav_title': 'Bombero #BOM-' + str(firefighter.id)
    }
    return render(request, 'firefighters/form.html', context)

@role_required(allowed_roles=['Administrador', 'Secretario Comandancia'])
@login_required(login_url='login')
def remove_firefighter(request, id):
    firefighter = Firefighter.objects.get(id=id)
    
    if request.method == 'POST':
        firefighter.delete()
        messages.success(request, '¡Bombero eliminado correctamente!', extra_tags='alert-success')
        return redirect('list_firefighters')
    
    context = {
        'firefighter': firefighter,
        'page_nav_title': 'Eliminar Bombero'
    }
    return render(request, 'firefighters/delete.html', context)


# 
# views.py (actual que ya tienes, ampliar con estas funciones)

@login_required(login_url='login')
def server_api_status(request):
    """API para obtener datos de estado en tiempo real"""
    data = {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "memory_used": round(psutil.virtual_memory().used / (1024 ** 3), 2),
        "memory_total": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "memory_free": round(psutil.virtual_memory().available / (1024 ** 3), 2),
        "disk_usage": get_disk_usage(),
        "uptime": get_uptime_seconds()
    }
    return JsonResponse(data)

@login_required(login_url='login')
def server_api_disk(request):
    """API para obtener información detallada del disco"""
    partitions = []
    for part in psutil.disk_partitions(all=False):
        if os.name == 'nt':
            if 'cdrom' in part.opts or part.fstype == '':
                continue
        usage = psutil.disk_usage(part.mountpoint)
        partitions.append({
            "device": part.device,
            "mountpoint": part.mountpoint,
            "fstype": part.fstype,
            "total": bytes_to_gb(usage.total),
            "used": bytes_to_gb(usage.used),
            "free": bytes_to_gb(usage.free),
            "percent": usage.percent
        })
    return JsonResponse({"partitions": partitions})

@login_required(login_url='login')
def server_api_network(request):
    """API para obtener información de red"""
    # Esta función requeriría permisos elevados o usar bibliotecas específicas
    # para obtener información detallada de red
    # Aquí proporcionamos datos simulados
    data = {
        "interfaces": [
            {
                "name": "eth0",
                "ip": socket.gethostbyname(socket.gethostname()),
                "netmask": "255.255.255.0",
                "gateway": "10.244.11.1"
            }
        ],
        "open_ports": [
            {"port": 22, "protocol": "TCP", "service": "SSH", "status": "Open"},
            {"port": 80, "protocol": "TCP", "service": "HTTP", "status": "Open"},
            {"port": 443, "protocol": "TCP", "service": "HTTPS", "status": "Open"}
        ]
    }
    return JsonResponse(data)

@login_required(login_url='login')
def server_api_logs(request):
    """API para obtener logs del sistema"""
    log_type = request.GET.get('type', 'system')
    log_level = request.GET.get('level', 'all')
    
    # Aquí deberías implementar la lógica para leer logs reales
    # Este es un ejemplo simulado
    logs = []
    
    # Simular diferentes tipos de logs
    if log_type == 'system':
        log_file = '/var/log/syslog'
    elif log_type == 'application':
        log_file = '/var/log/application.log'
    elif log_type == 'security':
        log_file = '/var/log/auth.log'
    else:
        log_file = f'/var/log/{log_type}.log'
    
    # En producción, deberías leer el archivo real
    logs = f"Logs de {log_type}, nivel {log_level}\nContenido simulado del archivo {log_file}"
    
    return JsonResponse({"logs": logs})

# Funciones auxiliares
def bytes_to_gb(bytes_val):
    """Convierte bytes a GB con formato"""
    return f"{bytes_val / (1024**3):.2f} GB"

def get_uptime_seconds():
    """Retorna el tiempo de actividad en segundos"""
    return int(time.time() - psutil.boot_time())

def get_disk_usage():
    """Obtiene el uso promedio de todos los discos"""
    usages = []
    for part in psutil.disk_partitions(all=False):
        if os.name == 'nt':
            if 'cdrom' in part.opts or part.fstype == '':
                continue
        usage = psutil.disk_usage(part.mountpoint)
        usages.append(usage.percent)
    
    return sum(usages) / len(usages) if usages else 0