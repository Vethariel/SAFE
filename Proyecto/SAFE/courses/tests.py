
import unittest
from courses.views import parse_evaluacion , is_txt_file
from django.core.files.uploadedfile import SimpleUploadedFile

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

