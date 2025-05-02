from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.models import ContentType
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Crea un superusuario si no existe y configura los grupos necesarios'

    def handle(self, *args, **kwargs):
        # Configuración del superusuario
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'zcdigital')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'jcurrinir@zcdigital.cl')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '126acbpa2021/31cbpa2025')

        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'El superusuario "{username}" ya existe.'))
            admin_user = User.objects.get(username=username)
        else:
            # Crear superusuario
            admin_user = User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Superusuario "{username}" creado exitosamente.'))
        
        # Crear o verificar existencia de grupo Administrador
        admin_group, created = Group.objects.get_or_create(name='Administrador')
        if created:
            self.stdout.write(self.style.SUCCESS('Grupo "Administrador" creado.'))
        
        # Asignar todos los permisos al grupo Administrador
        content_types = ContentType.objects.all()
        permissions = Permission.objects.filter(content_type__in=content_types)
        admin_group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS('Permisos asignados al grupo "Administrador".'))
        
        # Asegurar que el superusuario está en el grupo Administrador
        admin_user.groups.add(admin_group)
        self.stdout.write(self.style.SUCCESS(f'Usuario "{username}" añadido al grupo "Administrador".'))
        
        # Crear grupos adicionales del sistema
        groups = ['Superintendente', 'Comandante', 'Segundo Comandante', 'Tercer Comandante', 'Secretario General', 'Secretario Compañía', 'Mecánico']
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Grupo "{group_name}" creado.'))
            else:
                self.stdout.write(self.style.WARNING(f'Grupo "{group_name}" ya existía.'))