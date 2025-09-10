from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """カスタムユーザーモデルの管理画面設定"""
    
    # リスト表示するフィールド
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'created_at')
    
    # フィルター可能なフィールド
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'created_at')
    
    # 検索可能なフィールド
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    # 並び順
    ordering = ('-created_at',)
    
    # 詳細画面のフィールドセット
    fieldsets = UserAdmin.fieldsets + (
        ('追加情報', {
            'fields': ('profile_picture', 'created_at')
        }),
    )
    
    # 読み取り専用フィールド
    readonly_fields = ('created_at',)
    
    # 新規作成時のフィールドセット
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('追加情報', {
            'fields': ('email', 'profile_picture')
        }),
    )