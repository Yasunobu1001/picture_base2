"""
Gunicorn設定ファイル - 写真共有サイト用

本番環境でのGunicorn WSGIサーバー設定
パフォーマンス、セキュリティ、監視を考慮した設定
"""

import multiprocessing
import os

# サーバーソケット設定
bind = "127.0.0.1:8000"
backlog = 2048

# ワーカー設定
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# プロセス設定
preload_app = True
daemon = False
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# ログ設定
accesslog = "/var/log/gunicorn/photo_sharing_access.log"
errorlog = "/var/log/gunicorn/photo_sharing_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# プロセス名
proc_name = "photo_sharing_gunicorn"

# PIDファイル
pidfile = "/var/run/gunicorn/photo_sharing.pid"

# セキュリティ設定
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL設定（必要に応じて）
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# 環境変数
raw_env = [
    'DJANGO_SETTINGS_MODULE=photo_sharing_site.production_settings',
]

# ワーカープロセスのメモリ制限（オプション）
# worker_tmp_dir = "/dev/shm"  # RAMディスクを使用

# 監視・ヘルスチェック設定
def when_ready(server):
    """サーバー起動時の処理"""
    server.log.info("写真共有サイト Gunicornサーバーが起動しました")

def worker_int(worker):
    """ワーカープロセス中断時の処理"""
    worker.log.info("ワーカープロセス %s が中断されました", worker.pid)

def pre_fork(server, worker):
    """ワーカープロセス作成前の処理"""
    server.log.info("ワーカープロセス %s を作成中", worker.pid)

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
    worker.log.info("ワーカープロセス %s が異常終了しました", worker.pid)