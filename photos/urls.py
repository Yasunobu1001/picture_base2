"""
写真管理アプリのURL設定

写真のアップロード、表示、編集、削除に関連するすべてのURLパターンを定義します。
URL構造:
- /photos/ - ユーザーの写真一覧（マイギャラリー）
- /photos/upload/ - 写真アップロード
- /photos/public/ - 公開ギャラリー
- /photos/<id>/ - 写真詳細表示
- /photos/<id>/edit/ - 写真編集
- /photos/<id>/delete/ - 写真削除
"""
from django.urls import path
from . import views

app_name = 'photos'

urlpatterns = [
    # ギャラリー表示
    path('', views.PhotoListView.as_view(), name='list'),
    path('public/', views.PublicGalleryView.as_view(), name='public_gallery'),
    
    # 写真管理
    path('upload/', views.PhotoUploadView.as_view(), name='upload'),
    path('<int:pk>/', views.PhotoDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.PhotoUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.PhotoDeleteView.as_view(), name='delete'),
    
    # 将来的に追加予定の機能
    # path('search/', views.PhotoSearchView.as_view(), name='search'),
    # path('tag/<str:tag>/', views.PhotosByTagView.as_view(), name='by_tag'),
    # path('user/<str:username>/', views.UserPhotosView.as_view(), name='user_photos'),
    # path('<int:pk>/like/', views.PhotoLikeView.as_view(), name='like'),
    # path('<int:pk>/download/', views.PhotoDownloadView.as_view(), name='download'),
]