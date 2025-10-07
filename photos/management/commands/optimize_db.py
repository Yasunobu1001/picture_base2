"""
データベース最適化管理コマンド
"""
from django.core.management.base import BaseCommand
from django.db import connection
from photos.db_optimization import DatabaseOptimizer, CacheOptimizer
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'データベースを最適化し、パフォーマンス情報を表示します'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='クエリパフォーマンスを分析'
        )
        parser.add_argument(
            '--optimize',
            action='store_true',
            help='データベースを最適化'
        )
        parser.add_argument(
            '--cache',
            action='store_true',
            help='キャッシュを更新'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='すべての最適化を実行'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('データベース最適化を開始します...')
        )
        
        if options['all'] or options['analyze']:
            self.analyze_performance()
        
        if options['all'] or options['optimize']:
            self.optimize_database()
        
        if options['all'] or options['cache']:
            self.update_cache()
        
        self.stdout.write(
            self.style.SUCCESS('データベース最適化が完了しました。')
        )
    
    def analyze_performance(self):
        """パフォーマンス分析"""
        self.stdout.write('パフォーマンス分析中...')
        
        try:
            # テーブルサイズ情報
            table_sizes = DatabaseOptimizer.get_table_sizes()
            if table_sizes:
                self.stdout.write('\n=== テーブル統計情報 ===')
                for row in table_sizes:
                    self.stdout.write(f"テーブル: {row[1]}, カラム: {row[2]}, 重複度: {row[3]}")
            
            # インデックス使用状況
            index_usage = DatabaseOptimizer.get_index_usage()
            if index_usage:
                self.stdout.write('\n=== インデックス使用状況 ===')
                for row in index_usage:
                    self.stdout.write(f"インデックス: {row[2]}, 読み取り: {row[3]}, フェッチ: {row[4]}")
            
            # 遅いクエリ
            slow_queries = DatabaseOptimizer.get_slow_queries()
            if slow_queries:
                self.stdout.write('\n=== 遅いクエリ（100ms以上） ===')
                for row in slow_queries:
                    self.stdout.write(f"平均時間: {row[4]:.2f}ms, 呼び出し回数: {row[1]}")
                    self.stdout.write(f"クエリ: {row[0][:100]}...")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'パフォーマンス分析エラー: {e}')
            )
    
    def optimize_database(self):
        """データベース最適化"""
        self.stdout.write('データベース最適化中...')
        
        try:
            optimizations = DatabaseOptimizer.optimize_database()
            for optimization in optimizations:
                self.stdout.write(f'✓ {optimization}')
            
            self.stdout.write(
                self.style.SUCCESS(f'{len(optimizations)}個の最適化を実行しました。')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'データベース最適化エラー: {e}')
            )
    
    def update_cache(self):
        """キャッシュ更新"""
        self.stdout.write('キャッシュ更新中...')
        
        try:
            cache_results = CacheOptimizer.cache_photo_counts()
            self.stdout.write(f'✓ 公開写真数: {cache_results["public_count"]}')
            self.stdout.write(f'✓ 全写真数: {cache_results["total_count"]}')
            
            self.stdout.write(
                self.style.SUCCESS('キャッシュを更新しました。')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'キャッシュ更新エラー: {e}')
            )
    
    def show_connection_info(self):
        """データベース接続情報を表示"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            self.stdout.write(f'PostgreSQL バージョン: {version}')
            
            cursor.execute("SELECT current_database();")
            database = cursor.fetchone()[0]
            self.stdout.write(f'データベース: {database}')
            
            cursor.execute("SELECT count(*) FROM pg_stat_activity;")
            connections = cursor.fetchone()[0]
            self.stdout.write(f'アクティブ接続数: {connections}')