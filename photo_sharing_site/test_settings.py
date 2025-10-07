"""
テスト専用のDjango設定

PostgreSQLの代わりにSQLiteを使用してテストを高速化し、
データベース接続の問題を回避します。
"""

from .settings import *

# テスト用データベース設定（SQLite使用）
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # メモリ内データベースで高速化
    }
}

# テスト用メディアファイル設定
import tempfile
MEDIA_ROOT = tempfile.mkdtemp()

# テスト用ログ設定（ログを無効化して高速化）
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# テスト用パスワードハッシュ設定（高速化）
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',  # テスト用の高速ハッシュ
]

# テスト用キャッシュ設定
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# テスト用セキュリティ設定（一部無効化）
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# テスト用ファイルアップロード設定
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024  # 1MB（テスト用に小さく）
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024  # 1MB（テスト用に小さく）

# テスト用ミドルウェア設定（問題のあるミドルウェアを無効化）
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]