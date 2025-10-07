"""
アカウント管理アプリのURL設定

ユーザー認証に関連するすべてのURLパターンを定義します。
"""
from django.urls import path
from .views import SignUpView, CustomLoginView, CustomLogoutView

app_name = 'accounts'

urlpatterns = [
    # ユーザー認証
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    
    # 将来的に追加予定の機能
    # path('profile/', ProfileView.as_view(), name='profile'),
    # path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),
    # path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    # path('password/reset/', PasswordResetView.as_view(), name='password_reset'),
]