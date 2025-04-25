import time
import json
import psutil
import os
import platform
import django
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from datetime import datetime, timedelta
from .models import ServerStatus, Alert

# Umbrales para alertas
THRESHOLDS = {
    'cpu': {'warning': 70, 'critical': 90},
    'memory': {'warning': 80, 'critical': 95},
    'response_time': {'warning': 1000, 'critical': 3000},  # en ms
}

def create_alert(level, message):
    """Crea una alerta en la base de datos"""
    return Alert.objects.create(level=level, message=message)

@never_cache
def health_check(request):
    start_time = time.time()
    
    # Información básica del sistema
    system_info = {
        "app_name": "Intranet CBPA",
        "status": "ok",
        "environment": os.environ.get("ENVIRONMENT", "production"),
        "django_version": django.__version__,
        "python_version": platform.python_version(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "uptime": get_uptime(),
        "services": {}
    }
    
    # Verificar conexión a base de datos
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            db_connected = row[0] == 1
        
        db_info = {
            "status": "ok" if db_connected else "error",
            "type": connection.vendor,
            "name": connection.settings_dict["NAME"],
            "host": connection.settings_dict["HOST"] or "localhost"
        }
    except Exception as e:
        db_info = {
            "status": "error",
            "message": str(e),
            "type": connection.vendor if hasattr(connection, "vendor") else "unknown"
        }
        create_alert('critical', f"Error de conexión a la base de datos: {str(e)}")
    
    system_info["services"]["database"] = db_info
    
    # Verificar acceso a archivos estáticos
    static_root = os.environ.get("STATIC_ROOT", "")
    static_info = {
        "status": "ok" if os.path.exists(static_root) else "warning",
        "path": static_root
    }
    
    if static_info["status"] == "warning":
        create_alert('warning', f"STATIC_ROOT no configurado o no existe: {static_root}")
    
    system_info["services"]["static_files"] = static_info
    
    # Información de Digital Ocean
    do_info = {
        "status": "ok",
        "app_platform": True,
        "region": os.environ.get("REGION", "unknown")
    }
    
    system_info["services"]["digital_ocean"] = do_info
    
    # Verificar memoria y CPU
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        memory_info = {
            "status": get_status_level('memory', memory_usage),
            "total_mb": round(memory.total / (1024 * 1024), 2),
            "available_mb": round(memory.available / (1024 * 1024), 2),
            "used_percent": memory_usage
        }
        
        cpu_usage = psutil.cpu_percent(interval=0.1)
        cpu_info = {
            "status": get_status_level('cpu', cpu_usage),
            "usage_percent": cpu_usage,
            "count": psutil.cpu_count()
        }
        
        system_info["services"]["memory"] = memory_info
        system_info["services"]["cpu"] = cpu_info
        
        # Crear alertas basadas en umbrales
        if memory_info["status"] == "warning":
            create_alert('warning', f"Uso de memoria alto: {memory_usage}%")
        elif memory_info["status"] == "error":
            create_alert('critical', f"Uso de memoria crítico: {memory_usage}%")
            
        if cpu_info["status"] == "warning":
            create_alert('warning', f"Uso de CPU alto: {cpu_usage}%")
        elif cpu_info["status"] == "error":
            create_alert('critical', f"Uso de CPU crítico: {cpu_usage}%")
            
    except ImportError:
        system_info["services"]["system_resources"] = {"status": "unknown", "message": "psutil not installed"}
    
    # Estado general de la aplicación
    if any(service.get("status") == "error" for service in system_info["services"].values()):
        system_info["status"] = "error"
    elif any(service.get("status") == "warning" for service in system_info["services"].values()):
        system_info["status"] = "warning"
    
    # Calcular tiempo de respuesta
    end_time = time.time()
    response_time = (end_time - start_time) * 1000  # convertir a milisegundos
    system_info["response_time"] = round(response_time, 2)
    
    response_time_status = get_status_level('response_time', response_time)
    system_info["response_time_status"] = response_time_status
    
    if response_time_status == "warning":
        create_alert('warning', f"Tiempo de respuesta lento: {response_time} ms")
    elif response_time_status == "error":
        create_alert('critical', f"Tiempo de respuesta crítico: {response_time} ms")
    
    # Guardar estado del servidor
    ServerStatus.objects.create(
        status=system_info["status"],
        response_time=response_time,
        cpu_usage=cpu_usage if 'cpu_usage' in locals() else None,
        memory_usage=memory_usage if 'memory_usage' in locals() else None,
    )
    
    # Obtener datos históricos
    historical_data = ServerStatus.objects.all()[:100]  # últimos 100 registros
    
    # Datos para gráficos
    chart_data = {
        'timestamps': [entry.timestamp.strftime('%H:%M:%S') for entry in historical_data[:24]],
        'cpu': [entry.cpu_usage or 0 for entry in historical_data[:24]],
        'memory': [entry.memory_usage or 0 for entry in historical_data[:24]],
        'response_time': [entry.response_time for entry in historical_data[:24]],
    }
    
    # Invertir listas para mostrar datos cronológicamente
    for key in chart_data:
        chart_data[key].reverse()
    
    # Obtener alertas recientes
    recent_alerts = Alert.objects.filter(resolved=False)[:10]
    
    # Determinar formato de respuesta
    if request.GET.get('format') == 'json':
        return JsonResponse(system_info)
    else:
        return render(request, 'health_dashboard.html', {
            'data': system_info,
            'historical_data': historical_data[:10],  # Últimos 10 registros
            'chart_data': json.dumps(chart_data),
            'alerts': recent_alerts,
            'uptime': get_uptime(),
        })

def get_status_level(metric, value):
    """Determina el nivel de status basado en umbrales"""
    if metric in THRESHOLDS:
        if value >= THRESHOLDS[metric]['critical']:
            return "error"
        elif value >= THRESHOLDS[metric]['warning']:
            return "warning"
    return "ok"

def get_uptime():
    """Obtiene una estimación del tiempo de actividad basada en ServerStatus"""
    try:
        first_record = ServerStatus.objects.order_by('timestamp').first()
        if first_record:
            delta = datetime.now() - first_record.timestamp.replace(tzinfo=None)
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{days}d {hours}h {minutes}m"
        return "Desconocido"
    except:
        return "Desconocido"

@never_cache
def resolve_alert(request, alert_id):
    """Marca una alerta como resuelta"""
    try:
        alert = Alert.objects.get(id=alert_id)
        alert.resolved = True
        alert.resolved_at = datetime.now()
        alert.save()
        return JsonResponse({"status": "ok"})
    except Alert.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Alerta no encontrada"}, status=404)