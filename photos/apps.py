from django.apps import AppConfig


class PhotosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'photos'

    def ready(self):
        # Import signals to ensure handlers are registered
        from . import signals  # noqa: F401
