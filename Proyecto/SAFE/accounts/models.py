from django.db import models
from django.contrib.auth.models import AbstractUser

class AppUser(AbstractUser):
    """Usuario extendido con roles y estado"""
    
    class UserRole(models.TextChoices):
        COLABORADOR = 'colaborador', 'Colaborador'
        SUPERVISOR = 'supervisor', 'Supervisor'
        ANALISTA_TH = 'analistaTH', 'Analista TH'
    
    class UserStatus(models.TextChoices):
        ACTIVE = 'active', 'Activo'
        INACTIVE = 'inactive', 'Inactivo'
        PENDING = 'pending', 'Pendiente'
    
    # Sobrescribir campos heredados
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, verbose_name='name')
    last_name = models.CharField(max_length=100, verbose_name='last name')
    password = models.CharField(max_length=128, verbose_name='password')
    
    
    # Campos personalizados
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # last_login ya viene en AbstractUser
    
    class Meta:
        db_table = 'app_user'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.first_name} ({self.email})"