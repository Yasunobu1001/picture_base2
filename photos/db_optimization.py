"""
データベース最適化ユーティリティ
"""
from django.db import connection
from django.core.management.base import BaseCommand
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """データベース最適化クラス"""
    
    @staticmethod
    def analyze_query_performance():
        """クエリパフォーマンスを分析"""
        with connection.cursor() as cursor:
            # PostgreSQL固有のクエリ統計を取得
            cursor.execute("""
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements 
                WHERE query LIKE '%photo%' 
                ORDER BY total_time DESC 
                LIMIT 10;
            """)
            
            results = cursor.fetchall()
            return results
    
    @staticmethod
    def get_table_sizes():
        """テーブルサイズを取得"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats 
                WHERE tablename IN ('photos_photo', 'accounts_customuser')
                ORDER BY tablename, attname;
            """)
            
            results = cursor.fetchall()
            return results
    
    @staticmethod
    def get_index_usage():
        """インデックス使用状況を取得"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes 
                WHERE tablename IN ('photos_photo', 'accounts_customuser')
                ORDER BY idx_tup_read DESC;
            """)
            
            results = cursor.fetchall()
            return results
    
    @staticmethod
    def optimize_database():
        """データベースを最適化"""
        optimizations = []
        
        with connection.cursor() as cursor:
            # VACUUM ANALYZE を実行
            try:
                cursor.execute("VACUUM ANALYZE photos_photo;")
                optimizations.append("photos_photo テーブルをVACUUM ANALYZE")
                
                cursor.execute("VACUUM ANALYZE accounts_customuser;")
                optimizations.append("accounts_customuser テーブルをVACUUM ANALYZE")
                
            except Exception as e:
                logger.error(f"VACUUM ANALYZE エラー: {e}")
        
        return optimizations
    
    @staticmethod
    def get_slow_queries():
        """遅いクエリを取得"""
        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        (total_time/calls) as avg_time
                    FROM pg_stat_statements 
                    WHERE mean_time > 100  -- 100ms以上のクエリ
                    ORDER BY mean_time DESC 
                    LIMIT 5;
                """)
                
                results = cursor.fetchall()
                return results
                
            except Exception as e:
                logger.error(f"遅いクエリ取得エラー: {e}")
                return []


class QueryOptimizer:
    """クエリ最適化ヘルパー"""
    
    @staticmethod
    def optimize_photo_list_query(user=None, is_public=None):
        """写真一覧クエリを最適化"""
        from .models import Photo
        
        queryset = Photo.objects.select_related('owner')
        
        if user:
            queryset = queryset.filter(owner=user)
        
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public)
        
        # 必要なフィールドのみ取得
        queryset = queryset.only(
            'id', 'title', 'description', 'image', 'thumbnail',
            'is_public', 'created_at', 'owner__username'
        )
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def optimize_photo_detail_query(photo_id):
        """写真詳細クエリを最適化"""
        from .models import Photo
        
        return Photo.objects.select_related('owner').get(id=photo_id)
    
    @staticmethod
    def get_user_photo_count(user):
        """ユーザーの写真数を効率的に取得"""
        from .models import Photo
        
        return Photo.objects.filter(owner=user).count()
    
    @staticmethod
    def get_public_photo_count():
        """公開写真数を効率的に取得"""
        from .models import Photo
        
        return Photo.objects.filter(is_public=True).count()


class CacheOptimizer:
    """キャッシュ最適化クラス"""
    
    @staticmethod
    def cache_photo_counts():
        """写真数をキャッシュ"""
        from django.core.cache import cache
        from .models import Photo
        
        # 公開写真数をキャッシュ（1時間）
        public_count = Photo.objects.filter(is_public=True).count()
        cache.set('public_photo_count', public_count, 3600)
        
        # 全写真数をキャッシュ（1時間）
        total_count = Photo.objects.count()
        cache.set('total_photo_count', total_count, 3600)
        
        return {
            'public_count': public_count,
            'total_count': total_count
        }
    
    @staticmethod
    def get_cached_photo_count(cache_key, fallback_func):
        """キャッシュされた写真数を取得"""
        from django.core.cache import cache
        
        count = cache.get(cache_key)
        if count is None:
            count = fallback_func()
            cache.set(cache_key, count, 3600)  # 1時間キャッシュ
        
        return count


# パフォーマンス監視デコレータ
def monitor_query_performance(func):
    """クエリパフォーマンスを監視するデコレータ"""
    def wrapper(*args, **kwargs):
        from django.db import connection
        from django.conf import settings
        import time
        
        if settings.DEBUG:
            start_queries = len(connection.queries)
            start_time = time.time()
            
            result = func(*args, **kwargs)
            
            end_time = time.time()
            end_queries = len(connection.queries)
            
            query_count = end_queries - start_queries
            execution_time = end_time - start_time
            
            logger.info(
                f"{func.__name__}: {query_count} queries, "
                f"{execution_time:.3f}s execution time"
            )
            
            return result
        else:
            return func(*args, **kwargs)
    
    return wrapper