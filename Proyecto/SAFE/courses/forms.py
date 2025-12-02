# courses/forms.py
from django import forms
from django.core.validators import FileExtensionValidator
# Asumo que tu modelo se llama 'Course' en 'models.py'
# Si no es así, por favor avísame
from .models import Course 

# Opciones fijas para el nivel de dificultad
DIFFICULTY_CHOICES = [
    ('', 'Selecciona un nivel'),
    ('facil', 'Fácil'),
    ('media', 'Media'),
    ('dificil', 'Difícil'),
]

class QuestionUploadForm(forms.Form):
    
    # --- 1. Campo para "Seleccionar curso" ---
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        label="Seleccionar curso",
        empty_label="Selecciona un curso",
        widget=forms.Select(
            # Usamos la clase .input de tu login.css
            attrs={'class': 'input'} 
        )
    )

    # --- 2. Campo para "Nivel de dificultad" ---
    difficulty = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        label="Nivel de dificultad",
        widget=forms.Select(
            # Usamos la clase .input de tu login.css
            attrs={'class': 'input'}
        )
    )

    # --- 3. Campo para "Subir archivo" ---
    file = forms.FileField(
        label="Subir archivo",
        validators=[
            FileExtensionValidator(
                allowed_extensions=['txt'],
                message="Error: Solo se permiten archivos con extensión .txt"
            )
        ],
        # ¡IMPORTANTE! Usamos FileInput y le damos un ID
        # para conectarlo con JavaScript.
        # Lo esconderemos con CSS, no con HiddenInput.
        widget=forms.FileInput(
            attrs={'id': 'real-file-input', 'style': 'display: none;'}
        )
    )