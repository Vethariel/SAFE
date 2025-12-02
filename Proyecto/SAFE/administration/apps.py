from django.apps import AppConfig


class AdministrationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "administration"
    default = True

    def ready(self):
        import administration.signals  # pyright: ignore[reportMissingImports]  # noqa: F401
