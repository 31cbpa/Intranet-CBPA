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