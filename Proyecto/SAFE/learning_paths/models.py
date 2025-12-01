from django.db import models
from django.conf import settings
from courses.models import Course


class LearningPath(models.Model):
    """Rutas de aprendizaje"""

    class PathStatus(models.TextChoices):
        ACTIVE = "active", "Activo"
        DRAFT = "draft", "Borrador"
        ARCHIVED = "archived", "Archivado"

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    estimated_duration = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_paths",
    )
    header_img = models.ImageField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=PathStatus.choices, default=PathStatus.DRAFT
    )

    class Meta:
        db_table = "learning_path"
        verbose_name = "Ruta de aprendizaje"
        verbose_name_plural = "Rutas de aprendizaje"

    def __str__(self):
        return self.name


class CourseInPath(models.Model):
    """Relación entre cursos y rutas de aprendizaje"""

    learning_path = models.ForeignKey(
        LearningPath, on_delete=models.CASCADE, related_name="courses"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="in_paths"
    )
    previous_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="next_in_path",
    )
    next_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="previous_in_path",
    )

    class Meta:
        db_table = "course_in_path"
        verbose_name = "Curso en ruta"
        verbose_name_plural = "Cursos en rutas"
        unique_together = ("learning_path", "course")

    def __str__(self):
        return f"{self.course} en {self.learning_path}"
