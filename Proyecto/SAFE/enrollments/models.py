from decimal import Decimal
from django.db import models
from django.conf import settings
from courses.models import Course, Content
from learning_paths.models import LearningPath


class CourseInscription(models.Model):
    """Inscripción de usuarios en cursos"""

    class InscriptionStatus(models.TextChoices):
        ENROLLED = "enrolled", "Inscrito"
        IN_PROGRESS = "in_progress", "En progreso"
        COMPLETED = "completed", "Completado"
        FAILED = "failed", "Reprobado"
        WITHDRAWN = "withdrawn", "Retirado"

    app_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_inscriptions",
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="inscriptions"
    )
    enrollment_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    progress = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    status = models.CharField(
        max_length=20,
        choices=InscriptionStatus.choices,
        default=InscriptionStatus.ENROLLED,
    )

    class Meta:
        db_table = "course_inscription"
        verbose_name = "Inscripción a curso"
        verbose_name_plural = "Inscripciones a cursos"
        unique_together = ("app_user", "course")

    def __str__(self):
        return f"{self.app_user} - {self.course}"


class PathInscription(models.Model):
    """Inscripción de usuarios en rutas de aprendizaje"""

    class PathInscriptionStatus(models.TextChoices):
        ENROLLED = "enrolled", "Inscrito"
        IN_PROGRESS = "in_progress", "En progreso"
        COMPLETED = "completed", "Completado"
        WITHDRAWN = "withdrawn", "Retirado"

    app_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="path_inscriptions",
    )
    learning_path = models.ForeignKey(
        LearningPath, on_delete=models.CASCADE, related_name="inscriptions"
    )
    enrollment_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    progress = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    status = models.CharField(
        max_length=20,
        choices=PathInscriptionStatus.choices,
        default=PathInscriptionStatus.ENROLLED,
    )

    class Meta:
        db_table = "path_inscription"
        verbose_name = "Inscripción a ruta"
        verbose_name_plural = "Inscripciones a rutas"
        unique_together = ("app_user", "learning_path")

    def __str__(self):
        return f"{self.app_user} - {self.learning_path}"


class ContentProgress(models.Model):
    """Progreso del usuario en contenidos específicos"""

    content = models.ForeignKey(
        Content, on_delete=models.CASCADE, related_name="progress_records"
    )
    course_inscription = models.ForeignKey(
        CourseInscription, on_delete=models.CASCADE, related_name="content_progress"
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    file = models.BinaryField(null=True, blank=True)
    results = models.JSONField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        db_table = "content_progress"
        verbose_name = "Progreso de contenido"
        verbose_name_plural = "Progresos de contenidos"
        unique_together = ("content", "course_inscription")

    def __str__(self):
        return f"{self.course_inscription.app_user} - {self.content}"
