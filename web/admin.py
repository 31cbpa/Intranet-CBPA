from django.contrib import admin
from web.models import *


admin.site.register(Company)
admin.site.register(Vehicle)
admin.site.register(Repair)
admin.site.register(Part)
admin.site.register(RepairAttachment)
admin.site.register(PartAttachment)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    search_fields = ('user__username', 'user__email', 'role')

# Nuevas clases para Bomberos
class EmergencyContactInline(admin.TabularInline):
    model = EmergencyContact
    extra = 1
    fields = ('first_name', 'paternal_surname', 'maternal_surname', 'relationship', 'contact_number')

@admin.register(Firefighter)
class FirefighterAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'get_full_name', 'company', 'position', 'email')
    list_filter = ('company', 'position', 'entry_date')
    search_fields = ('first_name', 'paternal_surname', 'maternal_surname', 'registration_number', 'email', 'rut')
    inlines = [EmergencyContactInline]
    fieldsets = (
        ('Información institucional', {
            'fields': ('company', 'registration_number', 'entry_date', 'quality', 'position', 'email')
        }),
        ('Información personal', {
            'fields': ('first_name', 'paternal_surname', 'maternal_surname', 'rut', 'birth_date', 'gender', 
                      'address', 'commune', 'contact_number', 'personal_email')
        }),
    )
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.paternal_surname} {obj.maternal_surname}"
    
    get_full_name.short_description = 'Nombre completo'

@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'relationship', 'contact_number', 'get_firefighter')
    list_filter = ('relationship',)
    search_fields = ('first_name', 'paternal_surname', 'maternal_surname', 'firefighter__first_name')
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.paternal_surname} {obj.maternal_surname}"
    
    def get_firefighter(self, obj):
        return f"{obj.firefighter.first_name} {obj.firefighter.paternal_surname}"
    
    get_full_name.short_description = 'Nombre completo'
    get_firefighter.short_description = 'Bombero'