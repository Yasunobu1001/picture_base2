from django.core.files.storage import default_storage
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Photo


@receiver(post_delete, sender=Photo)
def delete_photo_files(sender, instance, **kwargs):
    """Remove associated files from storage when a photo is deleted."""
    for field_name in ["image", "thumbnail"]:
        file_field = getattr(instance, field_name, None)
        if not file_field:
            continue

        file_name = getattr(file_field, "name", "")
        if not file_name:
            continue

        try:
            if default_storage.exists(file_name):
                default_storage.delete(file_name)
        except Exception:
            # Swallow storage errors to avoid blocking delete operations
            pass
