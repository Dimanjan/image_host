from django.apps import AppConfig


class ImagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "images"

    def ready(self):
        """Apply debug SQL logging patch when app is ready"""
        from . import debug_sql_patch  # noqa
