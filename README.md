# 写真共有WEBサイト (Photo Sharing Website)

Django、PostgreSQL、Tailwind CSSを使用した写真共有プラットフォーム

## 🚀 セットアップ完了

このプロジェクトは以下のコンポーネントで構成されています：

### ✅ 完了した設定

1. **Django プロジェクト初期化**
   - Django 4.2.24
   - PostgreSQL データベース接続
   - 環境変数設定 (.env)

2. **データベース設定**
   - PostgreSQL 14
   - データベース: `photo_sharing_db`
   - マイグレーション完了

3. **Tailwind CSS 統合**
   - Tailwind CSS 3.x
   - カスタムコンポーネント定義
   - レスポンシブデザイン対応

4. **静的ファイル・メディアファイル設定**
   - WhiteNoise 統合
   - 静的ファイル収集設定
   - メディアファイルアップロード設定

5. **テンプレート構造**
   - ベーステンプレート作成
   - ホームページテンプレート
   - レスポンシブナビゲーション

## 📁 プロジェクト構造

```
picture_base/
├── photo_sharing_site/          # Django プロジェクト設定
│   ├── settings.py             # 設定ファイル
│   ├── urls.py                 # URL設定
│   └── wsgi.py                 # WSGI設定
├── templates/                   # HTMLテンプレート
│   ├── base.html               # ベーステンプレート
│   └── home.html               # ホームページ
├── static/                      # 静的ファイル
│   ├── css/
│   │   ├── input.css           # Tailwind入力ファイル
│   │   └── output.css          # コンパイル済みCSS
│   └── js/                     # JavaScript
├── media/                       # アップロードファイル
├── venv/                        # Python仮想環境
├── requirements.txt             # Python依存関係
├── package.json                 # Node.js依存関係
├── tailwind.config.js          # Tailwind設定
└── .env                        # 環境変数
```

## 🛠️ 開発コマンド

### Django コマンド
```bash
# 仮想環境アクティベート
source venv/bin/activate

# 開発サーバー起動
python manage.py runserver

# マイグレーション作成
python manage.py makemigrations

# マイグレーション実行
python manage.py migrate

# 静的ファイル収集
python manage.py collectstatic
```

### Tailwind CSS コマンド
```bash
# CSS監視モード（開発時）
npm run build-css

# CSS本番ビルド
npm run build-css-prod
```

## 🔧 環境設定

### 必要な環境変数 (.env)
```
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_NAME=photo_sharing_db
DATABASE_USER=postgres
DATABASE_PASSWORD=
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

### データベース設定
```bash
# PostgreSQL起動
brew services start postgresql@14

# データベース作成（既に完了）
createdb photo_sharing_db

# PostgreSQLユーザー作成（既に完了）
createuser -s postgres
```

## 📋 次のステップ

このセットアップが完了したので、以下のタスクに進むことができます：

1. **ユーザー認証システムの実装** (タスク 2.1-2.3)
2. **写真モデルとデータベース設計** (タスク 3.1-3.2)
3. **写真アップロード機能の実装** (タスク 4.1-4.3)

## 🧪 セットアップ検証

プロジェクトのセットアップを検証するには：

```bash
python verify_setup.py
```

## 📚 技術スタック

- **Backend**: Django 4.2.24
- **Database**: PostgreSQL 14
- **Frontend**: Tailwind CSS 3.x
- **Python**: 3.11
- **Node.js**: 24.7.0

## 🎯 要件対応

このセットアップは以下の要件に対応しています：
- Requirements 1.1: ユーザー認証基盤
- Requirements 2.1: 写真アップロード基盤
- Requirements 3.1: 写真表示基盤
- Requirements 6.1: レスポンシブデザイン基盤