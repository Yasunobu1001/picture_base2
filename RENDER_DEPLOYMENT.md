# Render デプロイ手順書

写真共有サイトをRenderにデプロイする完全ガイド

## 📋 目次

1. [事前準備](#事前準備)
2. [Renderアカウント設定](#renderアカウント設定)
3. [データベース作成](#データベース作成)
4. [Webサービスのデプロイ](#webサービスのデプロイ)
5. [環境変数の設定](#環境変数の設定)
6. [デプロイ後の確認](#デプロイ後の確認)
7. [トラブルシューティング](#トラブルシューティング)

---

## 事前準備

### 必要なもの

- ✅ GitHubアカウント
- ✅ Renderアカウント（無料プランでOK）
- ✅ このリポジトリがGitHubにプッシュされていること

### ファイル確認

以下のファイルが存在することを確認：

```
picture_base/
├── render.yaml                    # Render設定ファイル
├── build.sh                       # ビルドスクリプト
├── gunicorn_render.conf.py        # Gunicorn設定（Render用）
├── requirements.txt               # Python依存関係
├── photo_sharing_site/
│   ├── settings.py               # Django設定
│   └── wsgi.py                   # WSGIアプリケーション
└── manage.py                     # Django管理コマンド
```

---

## Renderアカウント設定

### 1. Renderにサインアップ

1. [Render](https://render.com/) にアクセス
2. **Get Started for Free** をクリック
3. GitHubアカウントで認証

### 2. GitHubリポジトリを連携

1. Renderダッシュボードで **New +** をクリック
2. **Blueprint** を選択
3. GitHubリポジトリ `picture_base2` を選択
4. リポジトリへのアクセスを許可

---

## データベース作成

### PostgreSQLデータベースの作成

#### 方法1: Blueprint経由（推奨）

`render.yaml` が自動的にデータベースを作成します。

#### 方法2: 手動作成

1. Renderダッシュボードで **New +** → **PostgreSQL** を選択
2. 以下の設定を入力：
   - **Name**: `photo-sharing-db`
   - **Database**: `photo_sharing_db`
   - **User**: `photo_sharing_user`
   - **Region**: `Oregon (US West)`
   - **Plan**: `Free` または `Starter`
3. **Create Database** をクリック

### データベース情報の確認

1. 作成したデータベースをクリック
2. **Internal Database URL** をコピー（後で使用）

---

## Webサービスのデプロイ

### 1. Blueprint経由でデプロイ（推奨）

`render.yaml` を使用した自動デプロイ：

1. Renderダッシュボードで **New +** → **Blueprint** を選択
2. リポジトリ `picture_base2` を選択
3. **Apply** をクリック
4. 自動的に以下が作成されます：
   - Web Service: `photo-sharing-web`
   - PostgreSQL: `photo-sharing-db`

### 2. 手動でWebサービスを作成

1. Renderダッシュボードで **New +** → **Web Service** を選択
2. GitHubリポジトリ `picture_base2` を選択
3. 以下の設定を入力：

| 項目 | 設定値 |
|------|--------|
| **Name** | `photo-sharing-web` |
| **Region** | `Oregon (US West)` |
| **Branch** | `main` |
| **Root Directory** | (空白) |
| **Runtime** | `Python 3` |
| **Build Command** | `./build.sh` |
| **Start Command** | `gunicorn --config gunicorn_render.conf.py photo_sharing_site.wsgi:application` |
| **Plan** | `Free` または `Starter` |

4. **Create Web Service** をクリック

---

## 環境変数の設定

### 必須の環境変数

Webサービスの **Environment** タブで以下を設定：

#### 1. Django基本設定

```bash
SECRET_KEY=<自動生成されたキー、または独自のキー>
DEBUG=False
PYTHON_VERSION=3.11.0
```

#### 2. ALLOWED_HOSTS

```bash
ALLOWED_HOSTS=<your-app-name>.onrender.com
```

例: `photo-sharing-web.onrender.com`

#### 3. データベース接続

```bash
DATABASE_URL=<PostgreSQLのInternal Database URL>
```

例: `postgresql://user:password@hostname:5432/database`

#### 4. スーパーユーザー作成（オプション）

初回デプロイ時にスーパーユーザーを自動作成する場合：

```bash
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=<強力なパスワード>
```

### 環境変数の設定手順

1. Webサービスのページで **Environment** タブをクリック
2. **Add Environment Variable** をクリック
3. Key と Value を入力
4. **Save Changes** をクリック

---

## デプロイ後の確認

### 1. デプロイステータスの確認

1. Webサービスのページで **Logs** タブを確認
2. 以下のメッセージが表示されればOK：
   ```
   ✅ ビルド完了！
   写真共有サイト Gunicornサーバーが起動しました (Render)
   ```

### 2. アプリケーションの動作確認

1. Webサービスのページで **URL** をクリック
   - 例: `https://photo-sharing-web.onrender.com`
2. ホームページが表示されることを確認

### 3. 管理画面へのアクセス

```
https://<your-app-name>.onrender.com/admin/
```

スーパーユーザーでログインして動作確認

### 4. ヘルスチェック

```
https://<your-app-name>.onrender.com/health/
```

ステータス200が返ればOK

---

## トラブルシューティング

### ❌ ビルドエラー

#### エラー: `Permission denied: ./build.sh`

**原因**: ビルドスクリプトに実行権限がない

**解決策**:
```bash
chmod +x build.sh
git add build.sh
git commit -m "build.shに実行権限を付与"
git push origin main
```

#### エラー: `ModuleNotFoundError: No module named 'dj_database_url'`

**原因**: `requirements.txt` に `dj-database-url` が含まれていない

**解決策**:
```bash
# requirements.txtに追加済みか確認
grep "dj-database-url" requirements.txt
```

### ❌ データベース接続エラー

#### エラー: `could not connect to server`

**原因**: `DATABASE_URL` が正しく設定されていない

**解決策**:
1. PostgreSQLデータベースの **Internal Database URL** をコピー
2. Webサービスの環境変数 `DATABASE_URL` に設定
3. **Save Changes** をクリック

### ❌ 静的ファイルが表示されない

#### エラー: CSS/JSが読み込まれない

**原因**: 静的ファイルが収集されていない

**解決策**:
1. `build.sh` に以下が含まれているか確認：
   ```bash
   python manage.py collectstatic --no-input
   ```
2. 再デプロイ

### ❌ 500 Internal Server Error

#### エラー: サーバーエラー

**原因**: 複数の可能性

**解決策**:
1. **Logs** タブでエラーログを確認
2. 環境変数 `DEBUG=True` に一時的に変更（デバッグ後は必ず `False` に戻す）
3. データベースマイグレーションを確認：
   ```bash
   # Render Shellで実行
   python manage.py showmigrations
   python manage.py migrate
   ```

### 🔧 Render Shell の使用

デバッグやメンテナンス用にShellを起動：

1. Webサービスのページで **Shell** タブをクリック
2. 以下のコマンドが使用可能：
   ```bash
   # マイグレーション状態の確認
   python manage.py showmigrations
   
   # マイグレーション実行
   python manage.py migrate
   
   # スーパーユーザー作成
   python manage.py createsuperuser
   
   # 静的ファイル収集
   python manage.py collectstatic
   ```

---

## 📊 パフォーマンス最適化

### 無料プランの制限

- **メモリ**: 512MB
- **CPU**: 共有
- **スリープ**: 15分間アクティビティがないとスリープ

### 推奨設定

#### 1. ワーカー数の調整

`gunicorn_render.conf.py` でワーカー数を調整：

```python
# 無料プランの場合は2ワーカー推奨
workers = int(os.environ.get('WEB_CONCURRENCY', 2))
```

環境変数で設定：
```bash
WEB_CONCURRENCY=2
```

#### 2. タイムアウトの調整

```bash
GUNICORN_TIMEOUT=120
```

---

## 🔄 継続的デプロイ

### 自動デプロイの設定

1. Webサービスの **Settings** タブをクリック
2. **Auto-Deploy** を `Yes` に設定
3. `main` ブランチにプッシュすると自動的にデプロイ

### 手動デプロイ

1. Webサービスのページで **Manual Deploy** をクリック
2. **Deploy latest commit** を選択

---

## 📝 チェックリスト

デプロイ前の最終確認：

- [ ] GitHubリポジトリにすべての変更がプッシュされている
- [ ] `render.yaml` が正しく設定されている
- [ ] `build.sh` に実行権限がある
- [ ] `requirements.txt` に全ての依存関係が含まれている
- [ ] 環境変数 `SECRET_KEY` が設定されている
- [ ] 環境変数 `DEBUG=False` が設定されている
- [ ] 環境変数 `ALLOWED_HOSTS` が設定されている
- [ ] 環境変数 `DATABASE_URL` が設定されている
- [ ] PostgreSQLデータベースが作成されている

---

## 🎉 デプロイ完了！

おめでとうございます！写真共有サイトがRenderにデプロイされました。

### 次のステップ

1. **カスタムドメインの設定**（オプション）
   - Webサービスの **Settings** → **Custom Domain** で設定

2. **環境変数の追加**（必要に応じて）
   - Redis URL
   - メール設定
   - AWS S3設定

3. **監視とログ**
   - Renderの **Logs** タブで定期的に確認
   - エラー監視ツール（Sentry等）の導入を検討

---

## 📚 参考リンク

- [Render公式ドキュメント](https://render.com/docs)
- [Django on Render](https://render.com/docs/deploy-django)
- [PostgreSQL on Render](https://render.com/docs/databases)
- [環境変数の管理](https://render.com/docs/environment-variables)

---

## 💬 サポート

問題が発生した場合：

1. このドキュメントの **トラブルシューティング** セクションを確認
2. Renderの **Logs** タブでエラーログを確認
3. [Render Community](https://community.render.com/) で質問
