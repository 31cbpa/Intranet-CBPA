from django.db import models
from django.contrib.auth.models import User
import json
from django.db.models.signals import post_save
from django.dispatch import receiver

class ServerStatus(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)  # ok, warning, error
    response_time = models.FloatField(default=0.0)  # en milisegundos
    cpu_usage = models.FloatField(null=True, blank=True)
    memory_usage = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.status}"
    
    @property
    def is_healthy(self):
        return self.status == 'ok'
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Server Status Entries"

class Alert(models.Model):
    LEVELS = (
        ('info', 'Información'),
        ('warning', 'Advertencia'),
        ('critical', 'Crítico'),
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=20, choices=LEVELS)
    message = models.TextField()
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.level} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    class Meta:
        ordering = ['-timestamp']

class Company(models.Model):
    name = models.CharField(max_length=256)
    address = models.CharField(max_length=256, null=True, blank=True)
    volunteers = models.IntegerField(null=True, blank=True)
    director = models.CharField(max_length=256, null=True, blank=True)
    contact = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return self.name
    

# Auth / Users
class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('administrador', 'Administrador'),
        ('superintendente', 'Superintendente'),
        ('secretario_comandancia', 'Secretario de Comandancia'),
        ('secretario_compania', 'Secretario de Compañía'),
        ('bombero', 'Bombero'),
        ('otro', 'Otro'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Compañía asignada")
    recovery_password_code = models.CharField(max_length=20, null=True, blank=True)
    recovery_password_expiration = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.email if self.user.email else self.user.username
    
    def can_edit_all_companies(self):
        return self.role in ['administrador', 'superintendente', 'secretario_comandancia']
    
    def can_edit_company(self, company_id):
        if self.can_edit_all_companies():
            return True
        return self.role == 'secretario_compania' and self.company and self.company.id == company_id
    
    def can_view_all(self):
        return self.role in ['administrador', 'superintendente']

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

class Vehicle(models.Model):
    car_code = models.CharField(max_length=32)
    car_type = models.CharField(max_length=32, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, null=True)
    license_plate = models.CharField(max_length=7)
    brand = models.CharField(max_length=256)
    model = models.CharField(max_length=256)
    year = models.IntegerField()
    technical_inspection = models.DateField()
    emissions_inspection = models.DateField()
    insurance = models.CharField(max_length=32)
    insurance_exp_date = models.DateField()
    vehicle_registration = models.DateField()

    def __str__(self):
        return self.car_code
        
class Repair(models.Model):
    title = models.CharField(max_length=256)
    status = models.CharField(max_length=32)
    resolution = models.TextField(blank=True, null=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    comments = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    # nueva implementación
    approval_message = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.title
        
class RepairAttachment(models.Model):
    repair = models.ForeignKey(Repair, on_delete=models.CASCADE)
    attachment = models.FileField(upload_to='attachments/')
    
    def __str__(self):
        return (self.attachment.name).replace('attachments/', '')
    
class Part(models.Model):
    repair = models.ForeignKey(Repair, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=256)
    value = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name
    
class PartAttachment(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    attachment = models.FileField(upload_to='attachments/')
    
    def __str__(self):
        return (self.attachment.name).replace('attachments/', '')

 # 
class Firefighter(models.Model):
    GENDER_CHOICES = (
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    )
    
    # Campos obligatorios
    company = models.ForeignKey(Company, on_delete=models.PROTECT, verbose_name="Compañía")
    registration_number = models.CharField(max_length=50, verbose_name="Número de registro", unique=True)
    entry_date = models.DateField(verbose_name="Fecha de ingreso")
    quality = models.CharField(max_length=100, verbose_name="Calidad")
    position = models.CharField(max_length=100, verbose_name="Cargo")
    email = models.EmailField(verbose_name="Correo electrónico", unique=True)
    
    # Datos personales obligatorios
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    paternal_surname = models.CharField(max_length=100, verbose_name="Apellido paterno")
    maternal_surname = models.CharField(max_length=100, verbose_name="Apellido materno")
    
    # Datos personales opcionales
    rut = models.CharField(max_length=12, blank=True, null=True, verbose_name="RUT")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Fecha de nacimiento")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True, verbose_name="Sexo")
    address = models.CharField(max_length=200, blank=True, null=True, verbose_name="Domicilio")
    commune = models.CharField(max_length=100, blank=True, null=True, verbose_name="Comuna")
    contact_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número de contacto")
    personal_email = models.EmailField(blank=True, null=True, verbose_name="Correo personal")
    
    # Si deseas vincular con el usuario del sistema
    user = models.OneToOneField(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='firefighter')
    
    def __str__(self):
        return f"{self.first_name} {self.paternal_surname} {self.maternal_surname} - {self.registration_number}"
    
    class Meta:
        verbose_name = "Bombero"
        verbose_name_plural = "Bomberos"
        ordering = ['company', 'registration_number']

class FirefighterDocument(models.Model):
    DOCUMENT_TYPES = (
        ('certificado', 'Certificado'),
        ('diploma', 'Diploma'),
        ('licencia', 'Licencia'),
        ('otro', 'Otro'),
    )
    
    firefighter = models.ForeignKey(Firefighter, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, verbose_name="Tipo de documento")
    name = models.CharField(max_length=200, verbose_name="Nombre del documento")
    issue_date = models.DateField(verbose_name="Fecha de emisión")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Fecha de vencimiento")
    file = models.FileField(upload_to='firefighter_documents/', verbose_name="Archivo")
    
    def __str__(self):
        return f"{self.name} - {self.firefighter}"
    
    class Meta:
        verbose_name = "Documento de bombero"
        verbose_name_plural = "Documentos de bomberos"

class EmergencyContact(models.Model):
    RELATIONSHIP_CHOICES = (
        ('Familiar', 'Familiar'),
        ('Amigo', 'Amigo'),
        ('Cónyuge', 'Cónyuge'),
        ('Otro', 'Otro'),
    )
    
    firefighter = models.ForeignKey(Firefighter, on_delete=models.CASCADE, related_name='emergency_contacts')
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    paternal_surname = models.CharField(max_length=100, verbose_name="Apellido paterno")
    maternal_surname = models.CharField(max_length=100, verbose_name="Apellido materno")
    relationship = models.CharField(max_length=50, choices=RELATIONSHIP_CHOICES, verbose_name="Parentesco")
    contact_number = models.CharField(max_length=20, verbose_name="Número de contacto")
    
    def __str__(self):
        return f"{self.first_name} {self.paternal_surname} {self.maternal_surname} - {self.relationship}"
    
    class Meta:
        verbose_name = "Contacto de emergencia"
        verbose_name_plural = "Contactos de emergencia"

