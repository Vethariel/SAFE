from django import forms
from courses.models import Course, Module, Content, Material, Exam, Assignment
from django.core.validators import FileExtensionValidator

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["name", "description", "duration_hours", "status", "header_img"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full",
                    "placeholder": "Título del curso",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "w-full",
                    "placeholder": "Descripción del curso",
                    "rows": 4,
                }
            ),
            "duration_hours": forms.NumberInput(
                attrs={
                    "class": "",
                    "min": 0,
                }
            ),
            "status": forms.Select(attrs={"class": ""}),
        }
        labels = {
            "name": "Título del curso",
            "description": "Descripción",
            "duration_hours": "Duración (horas)",
            "status": "Estado",
            "header_img": "Imagen de portada",
        }

    def clean_duration_hours(self):
        """Valida que la duración no sea negativa."""
        duration = self.cleaned_data.get("duration_hours")
        if duration is not None and duration < 0:
            raise forms.ValidationError("La duración no puede ser negativa.")
        return duration


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ["name", "description", "duration_hours"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "inline-input w-full",
                    "placeholder": "Nombre del nuevo módulo",
                    "style": "padding:12px;border-radius:8px;border:1px solid var(--safe-border);",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "w-full",
                    "placeholder": "Descripción del módulo (opcional)",
                    "rows": 3,
                }
            ),
            "duration_hours": forms.NumberInput(
                attrs={
                    "class": "",
                    "min": 0,
                }
            ),
        }
        labels = {
            "name": "Nombre",
            "description": "Descripción",
            "duration_hours": "Duración (horas)",
        }


class ContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ["title", "description", "block_type", "is_mandatory"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "w-full",
                    "placeholder": "Título del contenido",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "w-full",
                    "placeholder": "Descripción breve del contenido",
                    "rows": 4,
                }
            ),
            "block_type": forms.Select(
                attrs={
                    "class": "w-full",
                }
            ),
            "is_mandatory": forms.CheckboxInput(
                attrs={
                    "class": "checkbox-input",
                }
            ),
        }
        labels = {
            "title": "Título",
            "description": "Descripción",
            "block_type": "Tipo de bloque",
            "is_mandatory": "Contenido obligatorio",
        }


class MaterialForm(forms.ModelForm):
    # Campo oculto para especificar el tipo esperado según el block_type
    expected_type = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Material
        fields = ["file"]
        widgets = {
            "file": forms.FileInput(attrs={"class": ""}),
        }
        labels = {
            "file": "Archivo",
        }

    def clean(self):
        """Valida que la extensión del archivo coincida con el tipo esperado."""
        cleaned_data = super().clean()
        file = cleaned_data.get("file")
        expected_type = cleaned_data.get("expected_type")

        # Si no hay archivo nuevo, revisar el archivo existente de la instancia
        if not file and self.instance and self.instance.pk and self.instance.file:
            file = self.instance.file

        if file and expected_type:
            # Obtener la extensión del archivo
            filename = file.name if hasattr(file, "name") else str(file)
            if "." in filename:
                extension = filename.rsplit(".", 1)[-1].lower()
            else:
                raise forms.ValidationError(
                    {"file": "El archivo debe tener una extensión."}
                )

            # Mapeo de tipos esperados a extensiones válidas
            valid_extensions = {
                "jpg": ["jpg", "jpeg"],
                "mp4": ["mp4"],
                "pdf": ["pdf"],
                "mp3": ["mp3"],
                "txt": ["txt"],
            }

            # Verificar que la extensión coincida con el tipo esperado
            if expected_type in valid_extensions:
                if extension not in valid_extensions[expected_type]:
                    expected_display = expected_type.upper()
                    if expected_type == "jpg":
                        expected_display = "JPG/JPEG"
                    raise forms.ValidationError(
                        {
                            "file": f"El archivo debe ser de tipo {expected_display}. "
                            f"Has seleccionado un archivo {extension.upper()}."
                        }
                    )

        return cleaned_data

class ExamUploadForm(forms.Form):
    DIFFICULTY_CHOICES = [
        ('facil', 'Fácil'),
        ('media', 'Media'),
        ('dificil', 'Difícil'),
    ]

    # Título para el contenido (ej. "Examen Final")
    title = forms.CharField(
        label="Título del Examen",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ej. Examen Parcial'})
    )

    difficulty = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        label="Nivel de dificultad",
        widget=forms.Select(attrs={'class': 'input'})
    )

    file = forms.FileField(
        label="Archivo de preguntas (.txt)",
        validators=[
            FileExtensionValidator(
                allowed_extensions=['txt'],
                message="Solo se permiten archivos .txt"
            )
        ],
        widget=forms.FileInput(attrs={'style': 'display: none;', 'id': 'exam-file-input'})
    )