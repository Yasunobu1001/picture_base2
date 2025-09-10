# 技術スタック

## バックエンド
- **フレームワーク**: Django 4.2.24
- **データベース**: PostgreSQL 14
- **画像処理**: Pillow 10.1.0
- **静的ファイル**: WhiteNoise 6.6.0
- **環境管理**: python-decouple 3.8
- **データベースアダプター**: psycopg2-binary 2.9.9

## フロントエンド
- **CSSフレームワーク**: Tailwind CSS 4.1.13
- **フォームプラグイン**: @tailwindcss/forms 0.5.10
- **テンプレートエンジン**: Django Templates
- **言語**: 日本語（UI）、英語（コード）

## 開発環境
- **Python**: 3.11
- **Node.js**: 24.7.0
- **仮想環境**: venv
- **パッケージマネージャー**: npm

## よく使うコマンド

### Django開発
```bash
# 仮想環境を有効化
source venv/bin/activate

# 開発サーバーを起動
python manage.py runserver

# データベースマイグレーション
python manage.py makemigrations
python manage.py migrate

# 静的ファイルを収集
python manage.py collectstatic

# スーパーユーザーを作成
python manage.py createsuperuser
```

### フロントエンド開発
```bash
# CSS開発用のウォッチモード
npm run build-css

# 本番用CSSビルド
npm run build-css-prod
```

### データベースセットアップ
```bash
# PostgreSQLを開始（macOS with Homebrew）
brew services start postgresql@14

# データベースを作成
createdb photo_sharing_db

# ユーザーを作成
createuser -s postgres
```

### プロジェクト検証
```bash
# セットアップを検証
python verify_setup.py
```

## 環境設定

必要な `.env` 変数:
- `DEBUG`: 開発モードフラグ
- `SECRET_KEY`: Djangoシークレットキー
- `DATABASE_NAME`: PostgreSQLデータベース名
- `DATABASE_USER`: データベースユーザー
- `DATABASE_PASSWORD`: データベースパスワード
- `DATABASE_HOST`: データベースホスト
- `DATABASE_PORT`: データベースポート