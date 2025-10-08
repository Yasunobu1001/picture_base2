# 本番環境用Dockerfile
FROM python:3.11-slim

# 環境変数設定
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=photo_sharing_site.production_settings

# 作業ディレクトリ設定
WORKDIR /app

# システムパッケージ更新とインストール
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        libpq-dev \
        gcc \
        libjpeg-dev \
        zlib1g-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libwebp-dev \
        tcl8.6-dev \
        tk8.6-dev \
        python3-tk \
        libharfbuzz-dev \
        libfribidi-dev \
        libxcb1-dev \
    && rm -rf /var/lib/apt/lists/*

# 本番用requirements.txtをコピーしてインストール
COPY requirements-production.txt /app/
RUN pip install --no-cache-dir -r requirements-production.txt

# アプリケーションファイルをコピー（.dockerignoreで不要ファイルを除外）
COPY . /app/

# 静的ファイル用ディレクトリ作成
RUN mkdir -p /app/staticfiles /app/media

# 静的ファイル収集
RUN python manage.py collectstatic --noinput

# 非rootユーザー作成
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# ポート公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/', timeout=10)"

# アプリケーション起動
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "photo_sharing_site.wsgi:application"]