from django.db import models
from accounts.models import AppUser

# Create your models here.

class RoleChangeLog(models.Model):
    """Audit log for role changes between users."""

    changed_by = models.ForeignKey(
        AppUser, on_delete=models.CASCADE, related_name="role_changes_made"
    )
    target_user = models.ForeignKey(
        AppUser, on_delete=models.CASCADE, related_name="role_changes_received"
    )
    old_role = models.CharField(
        max_length=20, choices=AppUser.UserRole.choices, null=True, blank=True
    )
    new_role = models.CharField(max_length=20, choices=AppUser.UserRole.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de cambio de rol"
        verbose_name_plural = "Registros de cambio de rol"

    def __str__(self):
        return f"{self.changed_by} cambió el rol de {self.target_user}"