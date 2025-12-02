import os
from django.db.models import Sum
from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver
from courses.models import Material, Content, Course
from learning_paths.models import LearningPath, CourseInPath


def update_learning_path_duration(learning_path):
    """Recalcula la duración total de una ruta basada en sus cursos."""
    total_duration = learning_path.courses.aggregate(
        total=Sum("course__duration_hours")
    )["total"]
    learning_path.estimated_duration = total_duration or 0
    learning_path.save(update_fields=["estimated_duration"])


@receiver(post_save, sender=CourseInPath)
@receiver(post_delete, sender=CourseInPath)
def update_duration_on_path_change(sender, instance, **kwargs):
    update_learning_path_duration(instance.learning_path)


@receiver(post_save, sender=Course)
def update_duration_on_course_change(sender, instance, **kwargs):
    # Actualizar todas las rutas que contienen este curso
    paths = LearningPath.objects.filter(courses__course=instance).distinct()
    for path in paths:
        update_learning_path_duration(path)


@receiver(post_delete, sender=Content)
def auto_delete_material_on_content_delete(sender, instance, **kwargs):
    if instance.material_id:
        try:
            material = Material.objects.get(pk=instance.material_id)
            # verificar si el material ha quedado huérfano
            if not material.contents.exists():  # pyright: ignore[reportAttributeAccessIssue]
                material.delete()
        except Material.DoesNotExist:
            # material ya fue eliminado
            pass


@receiver(post_delete, sender=Material)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


@receiver(post_delete, sender=Course)
def auto_delete_course_image_on_delete(sender, instance, **kwargs):
    """Elimina la imagen de portada cuando se elimina el curso."""
    if instance.header_img:
        if os.path.isfile(instance.header_img.path):
            os.remove(instance.header_img.path)


@receiver(post_delete, sender=LearningPath)
def auto_delete_path_image_on_delete(sender, instance, **kwargs):
    """Elimina la imagen de portada cuando se elimina la ruta."""
    if instance.header_img:
        if os.path.isfile(instance.header_img.path):
            os.remove(instance.header_img.path)


@receiver(pre_save, sender=Material)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return False

    try:
        old_file = Material.objects.get(pk=instance.pk).file
    except Material.DoesNotExist:
        return False

    new_file = instance.file
    if not old_file == new_file:
        if old_file and os.path.isfile(old_file.path):
            os.remove(old_file.path)


@receiver(pre_save, sender=Course)
def auto_delete_course_image_on_change(sender, instance, **kwargs):
    """Elimina la imagen antigua cuando se actualiza la imagen del curso."""
    if not instance.pk:
        return False

    try:
        old_file = Course.objects.get(pk=instance.pk).header_img
    except Course.DoesNotExist:
        return False

    new_file = instance.header_img
    if not old_file == new_file:
        if old_file and os.path.isfile(old_file.path):
            os.remove(old_file.path)


@receiver(pre_save, sender=LearningPath)
def auto_delete_path_image_on_change(sender, instance, **kwargs):
    """Elimina la imagen antigua cuando se actualiza la imagen de la ruta."""
    if not instance.pk:
        return False

    try:
        old_file = LearningPath.objects.get(pk=instance.pk).header_img
    except LearningPath.DoesNotExist:
        return False

    new_file = instance.header_img
    if not old_file == new_file:
        if old_file and os.path.isfile(old_file.path):
            os.remove(old_file.path)
