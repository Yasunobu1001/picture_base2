from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    カスタムユーザーモデル
    Django標準のUserモデルを拡張してemailとprofile_pictureフィールドを追加
    """
    email = models.EmailField(unique=True, verbose_name="メールアドレス")
    profile_picture = models.ImageField(
        upload_to='profiles/', 
        blank=True, 
        null=True,
        verbose_name="プロフィール画像"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    class Meta:
        verbose_name = "ユーザー"
        verbose_name_plural = "ユーザー"

    def __str__(self):
        return self.username