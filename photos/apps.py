from django.apps import AppConfig


class PhotosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'photos'

    def ready(self):
        # Import signals to ensure handlers are registered
        from . import signals  # noqa: F401
        # Register HEIF/HEIC support for Pillow (iPhone photos)
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except Exception:
            # If the library is missing or fails to register, continue gracefully
            pass
