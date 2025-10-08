# 本番環境ファイル除外チェックリスト

## 概要
本番環境にデプロイする際に除外すべきファイルとディレクトリの一覧です。
セキュリティ、パフォーマンス、ストレージ効率の観点から重要です。

## 自動除外されるファイル

### 1. 開発・テスト用ファイル
- `verify_setup.py` - セットアップ検証スクリプト
- `test_*.py` - テストファイル
- `*_test.py` - テストファイル
- `*.test.py` - テストファイル
- `.coverage` - カバレッジレポート
- `htmlcov/` - HTMLカバレッジレポート
- `.pytest_cache/` - pytestキャッシュ

### 2. IDE・エディタ設定
- `.kiro/` - Kiro IDE設定
- `.vscode/` - Visual Studio Code設定
- `.idea/` - IntelliJ IDEA設定
- `*.swp`, `*.swo` - Vim一時ファイル

### 3. 環境・設定ファイル
- `.env` - 環境変数ファイル
- `.env.*` - 環境別設定ファイル
- `local_settings.py` - ローカル設定

### 4. ログ・一時ファイル
- `*.log` - ログファイル
- `*.tmp`, `*.temp` - 一時ファイル
- `*.bak`, `*.backup` - バックアップファイル

### 5. Node.js関連
- `node_modules/` - Node.jsパッケージ
- `npm-debug.log*` - npmデバッグログ
- `yarn-debug.log*` - Yarnデバッグログ

### 6. Python関連
- `__pycache__/` - Pythonキャッシュ
- `*.pyc`, `*.pyo` - コンパイル済みPython
- `venv/`, `env/` - 仮想環境

### 7. OS関連
- `.DS_Store` - macOS
- `Thumbs.db` - Windows
- `ehthumbs.db` - Windows

## 手動確認が必要なファイル

### 1. ドキュメント
- `README.md` - プロジェクト説明（本番では不要）
- `DEPLOYMENT.md` - デプロイ手順（本番では不要）
- `PRODUCTION_CHECKLIST.md` - 本チェックリスト（本番では不要）

### 2. 開発用スクリプト
- `deploy.py` - デプロイスクリプト（本番サーバーでは不要）

### 3. データベースファイル
- `*.sqlite3` - 開発用SQLiteファイル
- `*.db` - データベースファイル

### 4. SSL証明書
- `*.pem`, `*.key`, `*.crt` - 証明書ファイル（別途管理）

## 本番環境で必要なファイル

### 1. アプリケーションコード
- `manage.py` - Django管理スクリプト
- `photo_sharing_site/` - プロジェクト設定
- `photos/` - 写真アプリ
- `accounts/` - アカウントアプリ
- `templates/` - テンプレート

### 2. 設定ファイル
- `requirements-production.txt` - 本番用パッケージリスト
- `photo_sharing_site/production_settings.py` - 本番設定

### 3. 静的ファイル
- `staticfiles/` - 収集済み静的ファイル
- `static/css/output.css` - コンパイル済みCSS

### 4. Webサーバー設定
- `nginx.conf.template` - Nginx設定テンプレート

## デプロイ方法別の除外設定

### 1. Git デプロイ
`.gitignore`ファイルで自動除外

### 2. Docker デプロイ
`.dockerignore`ファイルで自動除外

### 3. rsync デプロイ
```bash
rsync -av --exclude-from=.gitignore \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='venv' \
  ./ user@server:/path/to/app/
```

### 4. 手動デプロイ
`python deploy.py --cleanup`で開発用ファイルを削除

## セキュリティ上の注意点

### 1. 機密情報の除外
- 環境変数ファイル（`.env`）
- データベース認証情報
- API キー・シークレット
- SSL秘密鍵

### 2. 開発用機能の無効化
- Django Debug Toolbar
- 開発用ミドルウェア
- テスト用エンドポイント

### 3. ログレベルの調整
- DEBUG → INFO/WARNING
- 機密情報のログ出力停止

## 自動化スクリプト

### デプロイ時の自動クリーンアップ
```bash
# 完全デプロイ（クリーンアップ含む）
python deploy.py --full

# クリーンアップのみ
python deploy.py --cleanup
```

### Docker ビルド
```bash
# 本番用イメージビルド（.dockerignoreで自動除外）
docker build -t photo-sharing-app .
```

## 確認コマンド

### ファイルサイズ確認
```bash
# プロジェクト全体のサイズ
du -sh .

# 除外後のサイズ（概算）
du -sh . --exclude='.git' --exclude='node_modules' --exclude='venv' --exclude='.kiro'
```

### 除外ファイル一覧
```bash
# .gitignoreに基づく除外ファイル確認
git ls-files --others --ignored --exclude-standard
```

## 本番環境でのファイル管理

### 1. ログファイル
- `/var/log/django/` - アプリケーションログ
- ログローテーション設定

### 2. メディアファイル
- `/app/media/` - アップロード済み写真
- 定期バックアップ設定

### 3. 静的ファイル
- `/app/staticfiles/` - 収集済み静的ファイル
- CDN配信推奨

## トラブルシューティング

### 1. 必要なファイルが除外された場合
- `.gitignore`や`.dockerignore`を確認
- 除外パターンを調整

### 2. 不要なファイルが含まれた場合
- デプロイスクリプトのクリーンアップ機能を実行
- 手動で削除

### 3. パーミッション問題
- ファイル所有者・権限を確認
- `chown`、`chmod`で調整

## 定期メンテナンス

### 1. 週次
- ログファイルのローテーション
- 一時ファイルの削除

### 2. 月次
- 不要なメディアファイルの削除
- データベース最適化

### 3. 四半期
- セキュリティ監査
- パフォーマンス最適化