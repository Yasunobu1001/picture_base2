"""
写真共有サイトのメインURL設定

このファイルはプロジェクト全体のURL構成を定義します。
各アプリケーションのURLは個別のurls.pyファイルで管理されています。
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve as static_serve
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from photos.health_check import health_check, health_check_detailed, readiness_check, liveness_check

def robots_txt(request):
    """robots.txtファイルを動的に生成"""
    lines = [
        "User-agent: *",
        "Allow: /",
        "Allow: /photos/public/",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /photos/upload/",
        "Disallow: /photos/*/edit/",
        "Disallow: /photos/*/delete/",
        "",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

urlpatterns = [
    # 管理画面
    path('admin/', admin.site.urls),
    
    # ホームページ
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
    # アプリケーションURL
    path('accounts/', include('accounts.urls')),
    path('photos/', include('photos.urls')),
    
    # SEO関連
    path('robots.txt', robots_txt, name='robots_txt'),
    
    # ヘルスチェック
    path('health/', health_check, name='health_check'),
    path('health/detailed/', health_check_detailed, name='health_check_detailed'),
    path('health/ready/', readiness_check, name='readiness_check'),
    path('health/live/', liveness_check, name='liveness_check'),
    
    # 静的ページ（将来的に追加予定）
    # path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    # path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    # path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    # path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
]

# 開発環境での静的ファイルとメディアファイルの配信
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # 開発環境でのデバッグツールバー（django-debug-toolbarがインストールされている場合）
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# In production, explicitly serve MEDIA via Django (small apps / Render)
if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
    ]

# カスタムエラーページ（本番環境用）
handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'
handler403 = 'django.views.defaults.permission_denied'
handler400 = 'django.views.defaults.bad_request'
