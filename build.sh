#!/usr/bin/env bash
# Render ビルドスクリプト
# Django アプリケーションのビルドとデプロイ準備

set -o errexit  # エラーが発生したら即座に終了

echo "=== Render ビルドスクリプト開始 ==="

# 依存関係のインストール
echo "📦 依存関係をインストール中..."
pip install --upgrade pip
pip install -r requirements.txt

# 静的ファイルの収集
echo "📁 静的ファイルを収集中..."
python manage.py collectstatic --no-input

# データベースマイグレーション
echo "🗄️  データベースマイグレーションを実行中..."
if python manage.py migrate --no-input; then
    echo "✅ マイグレーション成功"
else
    echo "❌ マイグレーション失敗"
    exit 1
fi

# スーパーユーザーの作成（環境変数が設定されている場合）
if [[ -n "$DJANGO_SUPERUSER_USERNAME" && -n "$DJANGO_SUPERUSER_EMAIL" && -n "$DJANGO_SUPERUSER_PASSWORD" ]]; then
    echo "👤 スーパーユーザーを作成中..."
    python manage.py createsuperuser --no-input --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" || echo "スーパーユーザーは既に存在します"
fi

echo "✅ ビルド完了！"
