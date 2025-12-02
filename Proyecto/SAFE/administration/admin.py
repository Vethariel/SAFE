from django.contrib import admin

# El usuario ya se registra en accounts/admin.py con UserAdmin personalizado.
# Si se necesita registrar otros modelos de 'administration', agréguelos aquí.
from accounts.models import AppUser
from .models import RoleChangeLog

@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'role', 'status', 'created_at')
    list_filter = ('role', 'status')
    search_fields = ('email', 'first_name')
    
    # Permite editar el rol directamente
    fieldsets = (
        ('Información básica', {
            'fields': ('username', 'email', 'first_name', 'last_name')
        }),
        ('Permisos y rol', {
            'fields': ('role', 'status', 'is_staff', 'is_superuser', 'is_active')
        }),
        ('Fechas', {
            'fields': ('last_login', 'date_joined')
        }),
    )

@admin.register(RoleChangeLog)
class RoleChangeLogAdmin(admin.ModelAdmin):
    list_display = ("changed_by", "target_user", "old_role", "new_role", "created_at")
    list_filter = ("new_role", "old_role")
    search_fields = (
        "changed_by__username",
        "changed_by__email",
        "target_user__username",
        "target_user__email",
    )