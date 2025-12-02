from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.views import unique_email
import unittest

"""
Crear una función llamada “unique_email” que valide si un email es único en la base de datos.:
    El email debe ser único en la tabla de usuarios.
    La función debe recibir un email como parámetro y retornar True si es único, False en caso contrario.

Generar los test.
"""

User = get_user_model()


class UniqueEmailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Creamos un usuario que SÍ existe
        cls.user = User.objects.create(username="testuser", email="existe@safe.com")

    def test_unique_email_true(self):
        """Debe retornar True cuando el email existe."""
        result = unique_email("existe@safe.com")
        self.assertTrue(result)

    def test_unique_email_false(self):
        """Debe retornar False cuando el email NO existe."""
        result = unique_email("noexiste@safe.com")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model

from .password_validator import (
    is_valid_password,
    is_enough_length,
    has_uppercase,
    has_lowercase,
    has_digit,
    has_no_spaces,
)
import unittest

User = get_user_model()


class TestPasswordValidator(unittest.TestCase):
    def test_is_valid_password(self):
        """Test the main password validation function."""
        casos = [
            ("isShort", False),
            ("islowercase", False),
            ("ISUPPERCASE", False),
            ("Haventdigit", False),
            ("Havent space", False),
            ("Password1", True),
            ("ValidPass1", True),
        ]

        for entrada, esperado in casos:
            with self.subTest(entrada=entrada):
                self.assertEqual(is_valid_password(entrada), esperado)

    def test_has_no_spaces(self):
        casos = [
            ("haventspaceblank", True),
            ("have space blank", False),
        ]

        for entrada, esperado in casos:
            with self.subTest(entrada=entrada):
                self.assertEqual(has_no_spaces(entrada), esperado)

    def test_has_digit(self):
        casos = [
            ("haventdigit", False),
            ("havedigit8", True),
        ]

        for entrada, esperado in casos:
            with self.subTest(entrada=entrada):
                self.assertEqual(has_digit(entrada), esperado)

    def test_has_lowercase(self):
        casos = [
            ("ISUPPERCASE", False),
            ("islowercase", True),
        ]

        for entrada, esperado in casos:
            with self.subTest(entrada=entrada):
                self.assertEqual(has_lowercase(entrada), esperado)

    def test_has_uppercase(self):
        casos = [
            ("isUppercase", True),
            ("islowercase", False),
        ]

        for entrada, esperado in casos:
            with self.subTest(entrada=entrada):
                self.assertEqual(has_uppercase(entrada), esperado)

    def test_is_enough_length(self):
        casos = [
            ("", False),
            ("isShort", False),
            ("isEnough", True),
            ("isMaxEight", True),
        ]

        for entrada, esperado in casos:
            with self.subTest(entrada=entrada):
                self.assertEqual(is_enough_length(entrada), esperado)


class TestUniqueUsername(TestCase):
    def test_usernameIsUnique(self):
        # Given (Dado)
        username_1 = "usuario_unico"
        email_1 = "test1@correo.com"
        password_1 = "passwordseguro123"

        User.objects.create_user(
            username=username_1, email=email_1, password=password_1
        )

        # Verify first user exists
        self.assertEqual(User.objects.count(), 1)

        # When: Try to create duplicate username
        username_2 = "usuario_unico"
        email_2 = "test2@correo.com"
        password_2 = "otrapassword123"

        # Then: IntegrityError is raised
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(
                    username=username_2, email=email_2, password=password_2
                )

        # Verify only one user still exists
        self.assertEqual(User.objects.count(), 1)

        # And: Create user with different username succeeds
        User.objects.create_user(
            username="usuario_distinto",
            email="test3@correo.com",
            password="passwordfinal123",
        )

        # Verify we now have 2 users
        self.assertEqual(User.objects.count(), 2)


if __name__ == "__main__":
    unittest.main()
