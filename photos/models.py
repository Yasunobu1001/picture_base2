from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from .utils import validate_image_file, create_thumbnail, resize_image

User = get_user_model()


class Photo(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='photos/%Y/%m/%d/',
        validators=[validate_image_file]
    )
    thumbnail = models.ImageField(upload_to='thumbnails/%Y/%m/%d/', blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '写真'
        verbose_name_plural = '写真'
        # データベース最適化のためのインデックス
        indexes = [
            models.Index(fields=['-created_at'], name='photo_created_at_idx'),  # 作成日時降順
            models.Index(fields=['owner', '-created_at'], name='photo_owner_created_idx'),  # 所有者別作成日時
            models.Index(fields=['is_public', '-created_at'], name='photo_public_created_idx'),  # 公開状態別作成日時
            models.Index(fields=['owner', 'is_public'], name='photo_owner_public_idx'),  # 所有者別公開状態
        ]
    
    def __str__(self):
        return self.title or f'Photo {self.id}'
    
    def get_absolute_url(self):
        return reverse('photos:detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        """保存時に画像最適化とサムネイル自動生成"""
        # 新規作成または画像が変更された場合
        if not self.pk or (self.pk and self._state.adding is False):
            try:
                # 既存のオブジェクトの場合、画像が変更されたかチェック
                if self.pk:
                    old_photo = Photo.objects.get(pk=self.pk)
                    if old_photo.image == self.image:
                        # 画像が変更されていない場合はそのまま保存
                        super().save(*args, **kwargs)
                        return
                
                # 画像の最適化処理
                if self.image:
                    # 1. 画像をリサイズ・圧縮（最大1920x1080、品質85%）
                    optimized_image = resize_image(self.image, max_width=1920, max_height=1080, quality=85)
                    if optimized_image != self.image:
                        self.image = optimized_image
                    
                    # 2. サムネイル生成（300x300、品質80%）
                    thumbnail = create_thumbnail(self.image, size=(300, 300), quality=80)
                    if thumbnail:
                        self.thumbnail = thumbnail
                        
            except Exception as e:
                # 画像処理に失敗してもエラーにしない
                pass
        
        super().save(*args, **kwargs)
