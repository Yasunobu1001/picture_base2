"""
ヘルスチェック機能

本番環境での監視・ヘルスチェック用エンドポイント
システムの状態を確認し、問題を早期発見する
"""

from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import time
import os
import psutil
from photos.models import Photo
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


@never_cache
@require_http_methods(["GET"])
def health_check(request):
    """
    基本的なヘルスチェック
    システムが正常に動作しているかを確認
    """
    try:
        # データベース接続チェック
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return HttpResponse("OK", status=200)
    except Exception as e:
        return HttpResponse(f"ERROR: {str(e)}", status=500)


@never_cache
@require_http_methods(["GET"])
def health_check_detailed(request):
    """
    詳細なヘルスチェック
    各コンポーネントの状態を詳細に確認
    """
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'checks': {}
    }
    
    overall_status = True
    
    # データベースチェック
    try:
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM auth_user")
            user_count = cursor.fetchone()[0]
        
        db_response_time = (time.time() - start_time) * 1000
        
        health_status['checks']['database'] = {
            'status': 'healthy',
            'response_time_ms': round(db_response_time, 2),
            'user_count': user_count
        }
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        overall_status = False
    
    # キャッシュチェック
    try:
        start_time = time.time()
        cache_key = 'health_check_test'
        cache.set(cache_key, 'test_value', 60)
        cached_value = cache.get(cache_key)
        cache.delete(cache_key)
        
        cache_response_time = (time.time() - start_time) * 1000
        
        if cached_value == 'test_value':
            health_status['checks']['cache'] = {
                'status': 'healthy',
                'response_time_ms': round(cache_response_time, 2)
            }
        else:
            health_status['checks']['cache'] = {
                'status': 'unhealthy',
                'error': 'Cache value mismatch'
            }
            overall_status = False
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        overall_status = False
    
    # ファイルシステムチェック
    try:
        media_root = settings.MEDIA_ROOT
        static_root = settings.STATIC_ROOT
        
        # メディアディレクトリの書き込み権限チェック
        test_file = os.path.join(media_root, 'health_check_test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        
        # ディスク使用量チェック
        disk_usage = psutil.disk_usage(media_root)
        disk_usage_percent = (disk_usage.used / disk_usage.total) * 100
        
        health_status['checks']['filesystem'] = {
            'status': 'healthy',
            'media_root_writable': True,
            'disk_usage_percent': round(disk_usage_percent, 2),
            'disk_free_gb': round(disk_usage.free / (1024**3), 2)
        }
        
        # ディスク使用量が90%を超えている場合は警告
        if disk_usage_percent > 90:
            health_status['checks']['filesystem']['status'] = 'warning'
            health_status['checks']['filesystem']['warning'] = 'High disk usage'
    except Exception as e:
        health_status['checks']['filesystem'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        overall_status = False
    
    # メモリ使用量チェック
    try:
        memory = psutil.virtual_memory()
        memory_usage_percent = memory.percent
        
        health_status['checks']['memory'] = {
            'status': 'healthy',
            'usage_percent': memory_usage_percent,
            'available_gb': round(memory.available / (1024**3), 2)
        }
        
        # メモリ使用量が90%を超えている場合は警告
        if memory_usage_percent > 90:
            health_status['checks']['memory']['status'] = 'warning'
            health_status['checks']['memory']['warning'] = 'High memory usage'
    except Exception as e:
        health_status['checks']['memory'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # アプリケーション統計
    try:
        photo_count = Photo.objects.count()
        user_count = User.objects.count()
        recent_photos = Photo.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=1)  # 直近24時間
        ).count()
        
        health_status['checks']['application'] = {
            'status': 'healthy',
            'total_photos': photo_count,
            'total_users': user_count,
            'photos_last_24h': recent_photos
        }
    except Exception as e:
        health_status['checks']['application'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        overall_status = False
    
    # 全体的なステータス設定
    if not overall_status:
        health_status['status'] = 'unhealthy'
    elif any(check.get('status') == 'warning' for check in health_status['checks'].values()):
        health_status['status'] = 'warning'
    
    # HTTPステータスコード設定
    if health_status['status'] == 'unhealthy':
        status_code = 503  # Service Unavailable
    elif health_status['status'] == 'warning':
        status_code = 200  # OK but with warnings
    else:
        status_code = 200  # OK
    
    return JsonResponse(health_status, status=status_code)


@never_cache
@require_http_methods(["GET"])
def readiness_check(request):
    """
    レディネスチェック
    アプリケーションがリクエストを受け入れる準備ができているかを確認
    """
    try:
        # 重要なサービスの確認
        checks = []
        
        # データベース接続確認
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks.append("database")
        
        # 基本的なモデルアクセス確認
        User.objects.exists()
        checks.append("models")
        
        # キャッシュ確認
        cache.set('readiness_test', 'ok', 10)
        if cache.get('readiness_test') == 'ok':
            checks.append("cache")
        
        return JsonResponse({
            'status': 'ready',
            'checks_passed': checks,
            'timestamp': time.time()
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'status': 'not_ready',
            'error': str(e),
            'timestamp': time.time()
        }, status=503)


@never_cache
@require_http_methods(["GET"])
def liveness_check(request):
    """
    ライブネスチェック
    アプリケーションプロセスが生きているかを確認
    """
    try:
        # 基本的な応答確認
        current_time = time.time()
        
        return JsonResponse({
            'status': 'alive',
            'timestamp': current_time,
            'process_id': os.getpid()
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'status': 'dead',
            'error': str(e),
            'timestamp': time.time()
        }, status=500)