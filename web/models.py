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

# Auth / Users
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, blank=True, null=True)
    recovery_password_code = models.CharField(max_length=20, null=True, blank=True)
    recovery_password_expiration = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.email if self.user.email else self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

class Company(models.Model):
    name = models.CharField(max_length=256)
    address = models.CharField(max_length=256, null=True, blank=True)
    volunteers = models.IntegerField(null=True, blank=True)
    director = models.CharField(max_length=256, null=True, blank=True)
    contact = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return self.name
    
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



