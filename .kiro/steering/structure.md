# プロジェクト構造

## ディレクトリ構成

```
photo_sharing_site/
├── photo_sharing_site/          # Djangoプロジェクト設定
│   ├── __init__.py
│   ├── settings.py             # メイン設定ファイル
│   ├── urls.py                 # ルートURL設定
│   ├── wsgi.py                 # WSGIアプリケーション
│   └── asgi.py                 # ASGIアプリケーション
├── templates/                   # グローバルHTMLテンプレート
│   ├── base.html               # ナビゲーション付きベーステンプレート
│   └── home.html               # ホームページテンプレート
├── static/                      # 静的アセット（開発用）
│   ├── css/
│   │   ├── input.css           # Tailwindソースファイル
│   │   └── output.css          # コンパイル済みCSS
│   └── js/                     # JavaScriptファイル
├── staticfiles/                 # 収集済み静的ファイル（本番用）
├── media/                       # ユーザーアップロードファイル
├── venv/                        # Python仮想環境
├── .kiro/                       # Kiro設定
│   ├── steering/               # AIアシスタントガイダンス
│   └── specs/                  # プロジェクト仕様
├── requirements.txt             # Python依存関係
├── package.json                 # Node.js依存関係
├── tailwind.config.js          # Tailwind設定
├── manage.py                   # Django管理スクリプト
├── .env                        # 環境変数
└── verify_setup.py             # セットアップ検証スクリプト
```

## コード構成パターン

### Djangoアプリ
- 今後のDjangoアプリはプロジェクトルートに作成する
- 各アプリはDjangoの標準構造に従う:
  ```
  app_name/
  ├── __init__.py
  ├── models.py
  ├── views.py
  ├── urls.py
  ├── admin.py
  ├── apps.py
  ├── tests.py
  └── migrations/
  ```

### テンプレート
- グローバルテンプレートは `/templates/` に配置
- アプリ固有のテンプレートは `app_name/templates/app_name/` に配置
- すべてのテンプレートは `base.html` を継承
- UIテキストは日本語、技術用語は英語を使用

### 静的ファイル
- 開発用CSSは `/static/css/` に配置
- コンパイル/収集済みファイルは `/staticfiles/` に配置
- カスタムコンポーネントと共にTailwindユーティリティクラスを使用
- カスタムコンポーネントは `input.css` で `@layer components` を使用して定義

### メディアファイル
- ユーザーアップロードは `/media/` に保存
- モデル/目的別に整理（例: `photos/`, `avatars/`）

## 命名規則

### ファイル・ディレクトリ
- Pythonファイルは小文字とアンダースコアを使用
- CSSクラスとIDはケバブケースを使用
- DjangoモデルはPascalCaseを使用
- データベースフィールドとPython変数はsnake_caseを使用

### CSSクラス
- カスタムコンポーネント: `.btn-primary`, `.card`, `.form-input`
- レイアウトとスタイリングにはTailwindユーティリティを使用
- カスタムクラスには目的のプレフィックスを付ける（例: `btn-`, `form-`, `card-`）

### URL
- URLパターンには小文字とハイフンを使用
- 関連するURLはアプリ固有の `urls.py` ファイルにグループ化
- URLパターンには意味のある名前を使用

## 設定管理

### 設定
- メイン設定は `photo_sharing_site/settings.py` に記述
- 環境固有の値は `.env` に記述
- 環境変数管理には `python-decouple` を使用

### 静的ファイル
- WhiteNoiseが静的ファイル配信を処理
- npmスクリプトによるTailwind CSSコンパイル
- 本番用静的ファイルは `/staticfiles/` に収集

### データベース
- PostgreSQLをプライマリデータベースとして使用
- マイグレーションは各アプリの `migrations/` ディレクトリで追跡
- すべてのデータベース操作にはDjango ORMを使用