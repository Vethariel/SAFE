import unittest
from unittest.mock import MagicMock
from courses.models import Material, Content, Course
from administration.forms import CourseForm, ContentForm
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from .forms import ExamUploadForm
from accounts.models import AppUser
from administration.models import RoleChangeLog
from django.contrib.auth import get_user_model
from .services import change_role
User = get_user_model()


class MaterialTypeInferenceTests(unittest.TestCase):
    """Tests para la inferencia del tipo de Material a partir de la extensión de archivo."""

    def _material_with_filename(self, filename, material_type=None):
        mock_file = MagicMock()
        mock_file.name = filename
        return Material(file=mock_file, type=material_type)

    def test_infiere_tipo_para_extensiones_soportadas(self):
        casos = [
            ("documento.pdf", "pdf"),
            ("DOCUMENTO.PDF", "pdf"),
            ("imagen.jpg", "jpg"),
            ("IMAGEN.JPG", "jpg"),
            ("video.mp4", "mp4"),
            ("VIDEO.MP4", "mp4"),
            ("audio.mp3", "mp3"),
            ("AUDIO.MP3", "mp3"),
            ("texto.txt", "txt"),
            ("TEXTO.TXT", "txt"),
        ]

        for filename, tipo_esperado in casos:
            with self.subTest(filename=filename):
                material = self._material_with_filename(filename)
                material.infer_type_from_file()

                self.assertEqual(material.type, tipo_esperado)

    def test_no_infiere_tipo_si_no_hay_archivo(self):
        material = Material(file=None, type=None)

        material.infer_type_from_file()

        self.assertIsNone(material.type)

    def test_no_infiere_tipo_si_ya_esta_definido(self):
        material = self._material_with_filename("documento.pdf", material_type="docx")

        material.infer_type_from_file()

        # Debe respetar el tipo ya definido, no sobrescribirlo.
        self.assertEqual(material.type, "docx")

    def test_extensiones_no_soportadas_no_asignan_tipo(self):
        casos = [
            "archivo.bin",
            "archivo",
            "archivo.tar.gz",
            "archivo.docx",
            "archivo.xlsx",
            "archivo.zip",
            "archivo.rar",
            "imagen.jpeg",
            "imagen.gif",
            "video.avi",
        ]

        for filename in casos:
            with self.subTest(filename=filename):
                material = self._material_with_filename(filename)

                material.infer_type_from_file()

                self.assertIsNone(material.type)

    def test_nombres_archivo_con_caracteres_especiales(self):
        """Archivos con caracteres especiales en el nombre deben inferir tipo correctamente."""
        casos = [
            ("documento con espacios.pdf", "pdf"),
            ("archivo_con_guiones-bajos.jpg", "jpg"),
            ("archivo.múltiple.extensión.pdf", "pdf"),
            ("123-archivo-numerico.mp4", "mp4"),
            ("MAYÚSCULAS.PDF", "pdf"),
        ]

        for filename, tipo_esperado in casos:
            with self.subTest(filename=filename):
                material = self._material_with_filename(filename)
                material.infer_type_from_file()

                self.assertEqual(material.type, tipo_esperado)

    def test_archivos_sin_extension(self):
        """Archivos sin extensión no deben asignar tipo."""
        casos = [
            "archivo",
            "documento",
            "README",
            "Makefile",
        ]

        for filename in casos:
            with self.subTest(filename=filename):
                material = self._material_with_filename(filename)
                material.infer_type_from_file()

                self.assertIsNone(material.type)

    def test_multiples_puntos_en_nombre_archivo(self):
        """Solo la última extensión debe ser considerada."""
        casos = [
            ("archivo.backup.pdf", "pdf"),
            ("reporte.2024.01.15.jpg", "jpg"),
            ("video.final.v2.mp4", "mp4"),
        ]

        for filename, tipo_esperado in casos:
            with self.subTest(filename=filename):
                material = self._material_with_filename(filename)
                material.infer_type_from_file()

                self.assertEqual(material.type, tipo_esperado)


# Tests de CourseForm


class CourseFormValidationTests(unittest.TestCase):
    """Tests de validación para CourseForm."""

    def _build_form(self, **overrides):
        data = {
            "name": "Curso válido",
            "description": "Descripción de prueba",
            "duration_hours": 10,
            "status": Course.CourseStatus.ACTIVE,
        }
        data.update(overrides)
        return CourseForm(data=data)

    def test_nombre_obligatorio(self):
        casos = [
            ("Curso válido", True),
            ("", False),
            (" ", False),
            ("   ", False),
        ]

        for nombre, esperado_valido in casos:
            with self.subTest(nombre=nombre):
                form = self._build_form(name=nombre)

                self.assertEqual(form.is_valid(), esperado_valido)
                if not esperado_valido:
                    self.assertIn("name", form.errors)

    def test_nombre_limite_150_caracteres(self):
        casos = [
            ("", False, "vacío invalido"),
            (" ", False, "vacío invalido"),
            ("  ", False, "vacío invalido"),
            ("A", True, "1 carácter válido"),
            ("A" * 149, True, "149 caracteres válido"),
            ("A" * 150, True, "150 caracteres límite válido"),
            ("A" * 151, False, "151 caracteres excede límite"),
            ("A" * 999, False, "999 caracteres excede límite"),
        ]

        for nombre, esperado_valido, descripcion in casos:
            with self.subTest(longitud=len(nombre), descripcion=descripcion):
                form = self._build_form(name=nombre)

                self.assertEqual(form.is_valid(), esperado_valido)
                if not esperado_valido:
                    self.assertIn("name", form.errors)

    def test_duracion_valores_extremos(self):
        """Duración debe aceptar valores válidos y rechazar negativos (si hay validación)."""
        casos = [
            (0, True, "cero debe ser válido"),
            (1, True, "uno debe ser válido"),
            (100, True, "100 horas debe ser válido"),
            (9999, True, "9999 horas debe ser válido"),
            (-1, False, "negativo actualmente es inválido"),
            (-100, False, "negativo grande actualmente es inválido"),
        ]

        for duracion, esperado_valido, descripcion in casos:
            with self.subTest(duracion=duracion, descripcion=descripcion):
                form = self._build_form(duration_hours=duracion)

                self.assertEqual(form.is_valid(), esperado_valido)

    def test_caracteres_especiales_en_nombre(self):
        """Nombres con caracteres especiales deben ser aceptados."""
        casos = [
            ("Curso: Introducción", True),
            ("Curso #1", True),
            ("Curso (2024)", True),
            ("Curso & Taller", True),
            ("Curso con ñ", True),
            ("Курс на русском", True),
            ("课程名称", True),
            ("🚀 Curso Moderno", True),
        ]

        for nombre, esperado_valido in casos:
            with self.subTest(nombre=nombre):
                form = self._build_form(name=nombre)

                self.assertEqual(form.is_valid(), esperado_valido)


# Tests de ContentForm


class ContentFormValidationTests(unittest.TestCase):
    """Tests de validación para ContentForm."""

    def _build_form(self, **overrides):
        data = {
            "title": "Contenido de prueba",
            "description": "",
            "block_type": Content.BlockType.TEXT,
            "is_mandatory": False,
        }
        data.update(overrides)
        return ContentForm(data=data)

    def test_title_obligatorio(self):
        casos = [
            ("Contenido válido", True),
            ("", False),
            (" ", False),
            ("   ", False),
        ]

        for titulo, esperado_valido in casos:
            with self.subTest(title=titulo):
                form = self._build_form(title=titulo)

                self.assertEqual(form.is_valid(), esperado_valido)
                if not esperado_valido:
                    self.assertIn("title", form.errors)

    def test_title_limite_150_caracteres(self):
        casos = [
            ("", False, "vacío invalido"),
            (" ", False, "vacío invalido"),
            ("  ", False, "vacío invalido"),
            ("A", True, "1 carácter válido"),
            ("A" * 149, True, "149 caracteres válido"),
            ("A" * 150, True, "150 caracteres límite válido"),
            ("A" * 151, False, "151 caracteres excede límite"),
            ("A" * 999, False, "999 caracteres excede límite"),
        ]

        for titulo, esperado_valido, descripcion in casos:
            with self.subTest(longitud=len(titulo), descripcion=descripcion):
                form = self._build_form(title=titulo)

                self.assertEqual(form.is_valid(), esperado_valido)
                if not esperado_valido:
                    self.assertIn("title", form.errors)

    def test_caracteres_especiales_en_titulo(self):
        """Títulos con caracteres especiales deben ser aceptados."""
        casos = [
            ("Contenido: Introducción", True),
            ("Bloque #1", True),
            ("Módulo (avanzado)", True),
            ("Texto & ejemplos", True),
            ("Lección con ñ", True),
            ("Тема на русском", True),
            ("课程内容", True),
            ("📚 Lectura", True),
        ]

        for titulo, esperado_valido in casos:
            with self.subTest(titulo=titulo):
                form = self._build_form(title=titulo)

                self.assertEqual(form.is_valid(), esperado_valido)

    def test_combinaciones_campos_vacios_y_espacios(self):
        """Probar combinaciones de campos vacíos y solo espacios."""
        casos = [
            # (title, description, esperado_valido, descripcion_caso)
            ("", "", False, "ambos vacíos"),
            (" ", "", False, "title solo espacios"),
            ("Válido", "", True, "description vacío válido"),
            ("Válido", "   ", True, "description espacios válido"),
            ("  Válido  ", "Test", True, "title con espacios alrededor"),
        ]

        for titulo, descripcion, esperado_valido, desc_caso in casos:
            with self.subTest(descripcion=desc_caso):
                form = self._build_form(title=titulo, description=descripcion)

                self.assertEqual(form.is_valid(), esperado_valido)
                if not esperado_valido:
                    self.assertIn("title", form.errors)

class ExamUploadFormTests(TestCase):
    """
    Pruebas para el formulario de carga de exámenes en Administración.
    Valida que solo acepte .txt y requiera título y dificultad.
    """

    def test_upload_valid_txt_file(self):
        """
        Caso feliz: Archivo .txt, título y dificultad presentes.
        """
        file_content = b"Q:P1|Pregunta|1\nO:P1-A|Opcion|1"
        file = SimpleUploadedFile(
            "preguntas.txt",
            file_content, 
            content_type="text/plain"
        )
        
        # El formulario nuevo pide 'title' y 'difficulty', NO 'course'
        form_data = {
            'title': 'Examen Final de Prueba',
            'difficulty': 'media'
        }
        file_data = {'file': file}

        form = ExamUploadForm(form_data, file_data)

        self.assertTrue(form.is_valid(), f"El formulario debería ser válido. Errores: {form.errors}")

    def test_reject_invalid_extension_file(self):
        """
        Debe fallar si subo una imagen png.
        """
        file_content = b"Esto es una imagen falsa."
        file = SimpleUploadedFile(
            "imagen.png", 
            file_content, 
            content_type="image/png"
        )
        
        form_data = {
            'title': 'Examen con error',
            'difficulty': 'media'
        }
        file_data = {'file': file}

        form = ExamUploadForm(form_data, file_data)

        self.assertFalse(form.is_valid(), "El formulario debería rechazar .png")
        
        self.assertIn('file', form.errors)
        self.assertTrue(
            any("Solo se permiten archivos" in str(error) for error in form.errors['file']),
            f"No se encontró el mensaje de error esperado. Recibido: {form.errors['file']}"
        )

    def test_form_is_invalid_if_no_file_is_sent(self):
        form_data = {
            'title': 'Examen sin archivo',
            'difficulty': 'media'
        }
        file_data = {} # Sin archivo

        form = ExamUploadForm(form_data, file_data)

        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    def test_form_is_invalid_if_no_title(self):
        file = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")
        
        form_data = {
            'difficulty': 'media'
        }
        file_data = {'file': file}

        form = ExamUploadForm(form_data, file_data)

        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
class ChangeRoleServiceTests(TestCase):
    def setUp(self):
        self.analyst = User.objects.create_user(
            username="analyst",
            email="analyst@example.com",
            password="password123",
            first_name="Ana",
            last_name="Lista",
            role=AppUser.UserRole.ANALISTA_TH,
        )
        self.supervisor = User.objects.create_user(
            username="supervisor",
            email="supervisor@example.com",
            password="password123",
            first_name="Sue",
            last_name="Pervisora",
            role=AppUser.UserRole.SUPERVISOR,
        )
        self.collaborator = User.objects.create_user(
            username="collaborator",
            email="collaborator@example.com",
            password="password123",
            first_name="Cole",
            last_name="Laborador",
            role=AppUser.UserRole.COLABORADOR,
        )

    def test_permission_denied_for_non_analyst(self):
        result = change_role(
            actor=self.supervisor,
            target=self.collaborator,
            new_role=AppUser.UserRole.ANALISTA_TH,
        )

        self.assertFalse(result)
        self.collaborator.refresh_from_db()
        self.assertEqual(self.collaborator.role, AppUser.UserRole.COLABORADOR)

    def test_invalid_role_is_rejected(self):
        result = change_role(
            actor=self.analyst,
            target=self.collaborator,
            new_role="invalid_role",
        )

        self.assertFalse(result)
        self.collaborator.refresh_from_db()
        self.assertEqual(self.collaborator.role, AppUser.UserRole.COLABORADOR)

    def test_self_role_change_is_blocked(self):
        result = change_role(
            actor=self.analyst,
            target=self.analyst,
            new_role=AppUser.UserRole.SUPERVISOR,
        )

        self.assertFalse(result)
        self.analyst.refresh_from_db()
        self.assertEqual(self.analyst.role, AppUser.UserRole.ANALISTA_TH)

    def test_successful_role_update(self):
        result = change_role(
            actor=self.analyst,
            target=self.collaborator,
            new_role=AppUser.UserRole.SUPERVISOR,
        )

        self.assertTrue(result)
        self.collaborator.refresh_from_db()
        self.assertEqual(self.collaborator.role, AppUser.UserRole.SUPERVISOR)

        log_entry = RoleChangeLog.objects.get()
        self.assertEqual(log_entry.changed_by, self.analyst)
        self.assertEqual(log_entry.target_user, self.collaborator)
        self.assertEqual(log_entry.old_role, AppUser.UserRole.COLABORADOR)
        self.assertEqual(log_entry.new_role, AppUser.UserRole.SUPERVISOR)
