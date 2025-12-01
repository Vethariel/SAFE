
import unittest
from courses.views import parse_evaluacion, is_txt_file
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .forms import QuestionUploadForm
from .models import Content, Course, Module
from .services import (
    append_content_to_module,
    append_module_to_course,
    get_ordered_contents,
    get_ordered_modules,
    move_content,
    move_module,
)

# Create your tests here.
class TestParseEvaluacion(unittest.TestCase):
    ''' Tests para la función parse_evaluacion.
    parse_evaluacion debe convertir un texto con preguntas y opciones en un diccionario con la estructura adecuada
    dada para las evaluaciones. 
    Casos válidos:
    - Evaluación simple con dos preguntas y opciones correctas e incorrectas.
    Casos inválidos:
    - Opción sin pregunta previa.
    - Pregunta sin opción correcta.
    - Línea mal formada.
    '''


    def test_valido(self):
        casos = [
            (EVAL_SIMPLE_TXT, EVAL_SIMPLE_PARSED),
        ]

        for entrada, esperado in casos:
            with self.subTest(entrada=entrada[:40] + "..."):
                resultado = parse_evaluacion(entrada)

                self.assertEqual(len(resultado), len(esperado))

                for r_preg, e_preg in zip(resultado, esperado):
                    self.assertEqual(r_preg["id"], e_preg["id"])
                    self.assertEqual(r_preg["texto"], e_preg["texto"])
                    self.assertEqual(len(r_preg["opciones"]), len(e_preg["opciones"]))

                    for r_opt, e_opt in zip(r_preg["opciones"], e_preg["opciones"]):
                        self.assertEqual(r_opt["id"], e_opt["id"])
                        self.assertEqual(r_opt["texto"], e_opt["texto"])
                        self.assertEqual(r_opt["es_correcta"], e_opt["es_correcta"])

    def test_invalido(self):
        casos = [
            EVAL_OPCION_SIN_PREGUNTA,
            EVAL_PREGUNTA_SIN_CORRECTA,
            EVAL_LINEA_MAL_FORMADA,
        ]

        for entrada in casos:
            with self.subTest(entrada=entrada[:40] + "..."):
                with self.assertRaises(ValueError):
                    parse_evaluacion(entrada)



# Datos de prueba

EVAL_SIMPLE_TXT = """
Q:Q1|¿Cuál es la capital de Francia?
O:Q1A1|París|1
O:Q1A2|Madrid|0
O:Q1A3|Roma|0

Q:Q2|¿Cuánto es 2 + 2?
O:Q2A1|3|0
O:Q2A2|4|1
O:Q2A3|5|0
""".strip()

EVAL_SIMPLE_PARSED = [
    {
        "id": "Q1",
        "texto": "¿Cuál es la capital de Francia?",
        "opciones": [
            {"id": "Q1A1", "texto": "París", "es_correcta": True},
            {"id": "Q1A2", "texto": "Madrid", "es_correcta": False},
            {"id": "Q1A3", "texto": "Roma", "es_correcta": False},
        ],
    },
    {
        "id": "Q2",
        "texto": "¿Cuánto es 2 + 2?",
        "opciones": [
            {"id": "Q2A1", "texto": "3", "es_correcta": False},
            {"id": "Q2A2", "texto": "4", "es_correcta": True},
            {"id": "Q2A3", "texto": "5", "es_correcta": False},
        ],
    },
]

EVAL_OPCION_SIN_PREGUNTA = """
O:Q1A1|París|1
""".strip()

EVAL_PREGUNTA_SIN_CORRECTA = """
Q:Q1|Pregunta sin correcta
O:Q1A1|Opción 1|0
O:Q1A2|Opción 2|0
""".strip()

EVAL_LINEA_MAL_FORMADA = """
Q:Q1 Esto está mal porque no hay separador
O:Q1A1|Opción válida|1
""".strip()




class TestIsTxtFile(unittest.TestCase):
    def test_is_txt_file(self):
        # Los datos
        casos = [
            # nombre, content_type, esperado
            (SimpleUploadedFile("evaluacion.txt", b"contenido", content_type="text/plain"), True),
            (SimpleUploadedFile("evaluacion.TXT", b"contenido", content_type="text/plain"), True),
            (SimpleUploadedFile("evaluacion.pdf", b"%PDF", content_type="application/pdf"), False),
            (SimpleUploadedFile("evaluacion", b"sin_extension", content_type="text/plain"), False),
            ("no_es_archivo", False),  # ni siquiera tiene .name
        ]

        for entrada, esperado in casos:
            with self.subTest(entrada=getattr(entrada, "name", str(entrada))):
                self.assertEqual(is_txt_file(entrada), esperado)


class OrderingServicesTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(name="Course A")
        self.module = append_module_to_course(
            self.course, Module(name="Module 1", description="First")
        )

    def test_append_module_builds_chain(self):
        m1 = self.module
        m2 = append_module_to_course(
            self.course, Module(name="Module 2", description="Second")
        )
        m3 = append_module_to_course(
            self.course, Module(name="Module 3", description="Third")
        )

        ordered = get_ordered_modules(self.course)
        self.assertEqual([m1, m2, m3], ordered)

        m1.refresh_from_db()
        m2.refresh_from_db()
        m3.refresh_from_db()

        self.assertIsNone(m1.previous_module)
        self.assertEqual(m1.next_module, m2)
        self.assertEqual(m2.previous_module, m1)
        self.assertEqual(m2.next_module, m3)
        self.assertEqual(m3.previous_module, m2)
        self.assertIsNone(m3.next_module)

    def test_move_module_swaps_neighbors(self):
        m1 = self.module
        m2 = append_module_to_course(
            self.course, Module(name="Module 2", description="Second")
        )
        m3 = append_module_to_course(
            self.course, Module(name="Module 3", description="Third")
        )

        moved = move_module(m2, "up")
        self.assertTrue(moved)

        ordered = get_ordered_modules(self.course)
        self.assertEqual([m2, m1, m3], ordered)

        m1.refresh_from_db()
        m2.refresh_from_db()
        m3.refresh_from_db()

        self.assertIsNone(m2.previous_module)
        self.assertEqual(m2.next_module, m1)
        self.assertEqual(m1.previous_module, m2)
        self.assertEqual(m1.next_module, m3)
        self.assertEqual(m3.previous_module, m1)
        self.assertIsNone(m3.next_module)

    def test_append_content_sets_order_and_links(self):
        c1 = append_content_to_module(
            self.module,
            Content(
                title="One",
                description="c1",
                block_type=Content.BlockType.TEXT,
                content_type=Content.ContentType.MATERIAL,
            ),
        )
        c2 = append_content_to_module(
            self.module,
            Content(
                title="Two",
                description="c2",
                block_type=Content.BlockType.TEXT,
                content_type=Content.ContentType.MATERIAL,
            ),
        )
        c3 = append_content_to_module(
            self.module,
            Content(
                title="Three",
                description="c3",
                block_type=Content.BlockType.TEXT,
                content_type=Content.ContentType.MATERIAL,
            ),
        )

        ordered = get_ordered_contents(self.module)
        self.assertEqual([c1, c2, c3], ordered)
        self.assertEqual([1, 2, 3], [c.order for c in ordered])

        c1.refresh_from_db()
        c2.refresh_from_db()
        c3.refresh_from_db()

        self.assertIsNone(c1.previous_content)
        self.assertEqual(c1.next_content, c2)
        self.assertEqual(c2.previous_content, c1)
        self.assertEqual(c2.next_content, c3)
        self.assertEqual(c3.previous_content, c2)
        self.assertIsNone(c3.next_content)

    def test_move_content_updates_order(self):
        c1 = append_content_to_module(
            self.module,
            Content(
                title="One",
                description="c1",
                block_type=Content.BlockType.TEXT,
                content_type=Content.ContentType.MATERIAL,
            ),
        )
        c2 = append_content_to_module(
            self.module,
            Content(
                title="Two",
                description="c2",
                block_type=Content.BlockType.TEXT,
                content_type=Content.ContentType.MATERIAL,
            ),
        )
        c3 = append_content_to_module(
            self.module,
            Content(
                title="Three",
                description="c3",
                block_type=Content.BlockType.TEXT,
                content_type=Content.ContentType.MATERIAL,
            ),
        )

        moved = move_content(c2, "down")
        self.assertTrue(moved)

        ordered = get_ordered_contents(self.module)
        self.assertEqual([c1, c3, c2], ordered)
        self.assertEqual([1, 2, 3], [c.order for c in ordered])

        c1.refresh_from_db()
        c2.refresh_from_db()
        c3.refresh_from_db()

        self.assertEqual(c1.next_content, c3)
        self.assertEqual(c3.previous_content, c1)
        self.assertEqual(c3.next_content, c2)
        self.assertEqual(c2.previous_content, c3)
        self.assertIsNone(c2.next_content)

