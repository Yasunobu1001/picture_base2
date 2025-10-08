"""
Gunicorn設定ファイル - Render用
写真共有サイト - 本番環境設定
"""

import multiprocessing
import os

# サーバーソケット設定
# Renderは環境変数PORTを提供するため、それを使用
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
backlog = 2048

# ワーカー設定
# Renderの無料プランは512MBメモリ制限があるため、ワーカー数を調整
workers = int(os.environ.get('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
timeout = 120  # Renderでは長めのタイムアウトを推奨
keepalive = 5
max_requests = 1000
max_requests_jitter = 100

# プロセス設定
preload_app = True
daemon = False

# ログ設定
# Renderは標準出力/標準エラー出力をキャプチャするため、"-"を使用
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# プロセス名
proc_name = "photo_sharing_render"

# セキュリティ設定
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 環境変数
raw_env = [
    'DJANGO_SETTINGS_MODULE=photo_sharing_site.settings',
]

# ワーカープロセスのメモリ制限
# Renderではメモリが限られているため、tmpディレクトリを指定
worker_tmp_dir = "/dev/shm"

# 監視・ヘルスチェック設定
def when_ready(server):
    """サーバー起動時の処理"""
    server.log.info("写真共有サイト Gunicornサーバーが起動しました (Render)")
    server.log.info(f"Workers: {workers}, Port: {os.environ.get('PORT', '10000')}")

def worker_int(worker):
    """ワーカープロセス中断時の処理"""
    worker.log.info("ワーカープロセス %s が中断されました", worker.pid)

def pre_fork(server, worker):
    """ワーカープロセス作成前の処理"""
    pass  # ログを減らしてパフォーマンス向上

def post_fork(server, worker):
    """ワーカープロセス作成後の処理"""
    server.log.info("ワーカープロセス %s が作成されました", worker.pid)

def pre_exec(server):
    """サーバー実行前の処理"""
    server.log.info("Gunicornサーバーを実行中")

def on_exit(server):
    """サーバー終了時の処理"""
    server.log.info("写真共有サイト Gunicornサーバーが終了しました")

def worker_abort(worker):
    """ワーカープロセス異常終了時の処理"""
    worker.log.error("ワーカープロセス %s が異常終了しました", worker.pid)
