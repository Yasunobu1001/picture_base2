# Design Document

## Overview

写真共有WEBサイトは、Django 4.2とPostgreSQLを使用したバックエンドと、Tailwind CSSでスタイリングされたフロントエンドを持つWebアプリケーションです。セキュリティ強化、パフォーマンス最適化、画像処理、レスポンシブデザインを統合した本格的なWebアプリケーションとして設計されています。

## Architecture

### システム構成
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Django App    │    │   PostgreSQL    │
│   (HTML/CSS/JS) │◄──►│   (Backend)     │◄──►│   (Database)    │
│   + Tailwind    │    │   + Media Files │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Django アプリケーション構造
- `accounts/` - ユーザー認証とプロフィール管理
- `photos/` - 写真のアップロード、管理、表示、セキュリティ機能
- `photo_sharing_site/` - プロジェクト設定とURL設定
- `static/` - CSS、JavaScript、画像ファイル
- `media/` - アップロードされた写真ファイル
- `templates/` - HTMLテンプレート

## Components and Interfaces

### 1. User Authentication System (accounts/)

**Models:**
- `CustomUser` - Django標準Userモデルを拡張
  - `email` (EmailField, unique=True)
  - `username` (CharField, unique=True)
  - `profile_picture` (ImageField, optional)
  - `created_at` (DateTimeField)

**Views:**
- `SignUpView` - ユーザー登録
- `LoginView` - ログイン
- `LogoutView` - ログアウト
- `ProfileView` - プロフィール表示・編集

**Templates:**
- `registration/signup.html`
- `registration/login.html`
- `accounts/profile.html`

### 2. Photo Management System (photos/)

**Models:**
- `Photo`
  - `title` (CharField, max_length=100)
  - `description` (TextField, blank=True)
  - `image` (ImageField, upload_to='photos/')
  - `owner` (ForeignKey to User)
  - `is_public` (BooleanField, default=True)
  - `created_at` (DateTimeField)
  - `updated_at` (DateTimeField)

**Views:**
- `PhotoListView` - 写真一覧表示（ページネーション付き、クエリ最適化）
- `PhotoDetailView` - 写真詳細表示（権限チェック、前後ナビゲーション）
- `PhotoUploadView` - 写真アップロード（セキュリティ検証、自動最適化）
- `PhotoUpdateView` - 写真情報編集（所有者権限チェック）
- `PhotoDeleteView` - 写真削除（確認ダイアログ、ファイル削除）
- `PublicGalleryView` - 公開写真ギャラリー（パフォーマンス最適化）

**Middleware:**
- `SecurityHeadersMiddleware` - セキュリティヘッダー追加
- `LoginAttemptMiddleware` - ログイン試行制限
- `SessionSecurityMiddleware` - セッションセキュリティ強化
- `FileUploadSecurityMiddleware` - ファイルアップロードセキュリティ
- `XSSProtectionMiddleware` - XSS攻撃防止

**Utilities:**
- `photos/utils.py` - 画像処理、バリデーション、セキュリティ機能
- `photos/db_optimization.py` - データベース最適化とパフォーマンス監視
- `photos/health_check.py` - システムヘルスチェック機能

**Templates:**
- `photos/photo_list.html`
- `photos/photo_detail.html`
- `photos/photo_upload.html`
- `photos/photo_edit.html`
- `photos/public_gallery.html`

### 3. セキュリティ・最適化機能 (photos/)

**セキュリティ機能:**
- `validate_image_file()` - 包括的な画像ファイル検証
- `sanitize_filename()` - ファイル名のサニタイズ
- セキュリティミドルウェア群 - 多層防御システム
- CSRF、XSS、セッションハイジャック対策

**パフォーマンス最適化:**
- `QueryOptimizer` - データベースクエリ最適化
- `CacheOptimizer` - キャッシュ戦略
- `monitor_query_performance` - パフォーマンス監視
- 遅延読み込み（Lazy Loading）

**画像処理:**
- `create_thumbnail()` - 高品質サムネイル生成
- `resize_image()` - 自動リサイズと圧縮
- `compress_image()` - ファイルサイズ最適化
- EXIF情報処理と回転補正

## Data Models

### User Model
```python
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Photo Model
```python
class Photo(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='photos/%Y/%m/%d/')
    thumbnail = models.ImageField(upload_to='thumbnails/%Y/%m/%d/', blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
```

### Database Schema
```sql
-- Users table (Django's auth_user + custom fields)
-- Photos table with foreign key to users
-- Indexes on created_at, owner, is_public for performance
```

## Error Handling

### File Upload Validation
- ファイル形式チェック（JPEG, PNG, GIF）
- ファイルサイズ制限（10MB）
- 画像の有効性検証
- 悪意のあるファイルの検出

### User Input Validation
- フォームバリデーション（Django Forms）
- CSRFトークン保護
- XSS攻撃防止
- SQLインジェクション防止（Django ORM使用）

### Error Pages
- 404 - ページが見つからない
- 403 - アクセス権限なし
- 500 - サーバーエラー
- カスタムエラーページ（Tailwind CSSでスタイリング）

## UI/UX Design

### Tailwind CSS Framework
- ユーティリティファーストのアプローチ
- レスポンシブデザイン（sm:, md:, lg:, xl: ブレークポイント）
- ダークモード対応（dark: プレフィックス）
- カスタムカラーパレット

### Component Design
- **Navigation Bar**: ロゴ、メニュー、ユーザーアイコン
- **Photo Grid**: レスポンシブなマソンリーレイアウト
- **Photo Cards**: サムネイル、タイトル、作者情報
- **Upload Modal**: ドラッグ&ドロップ対応
- **Photo Viewer**: フルサイズ表示、メタデータ表示

### Responsive Breakpoints
- Mobile: < 640px (1列グリッド)
- Tablet: 640px - 1024px (2-3列グリッド)
- Desktop: > 1024px (4-6列グリッド)

## Performance Optimization

### Image Handling
- 自動サムネイル生成（Pillow使用、高品質リサンプリング）
- 遅延読み込み（Lazy Loading）実装済み
- 画像圧縮と最適化（段階的品質調整）
- EXIF情報処理と自動回転補正
- 複数サイズ画像生成（レスポンシブ対応）

### Database Optimization
- 戦略的インデックス設定（作成日時、所有者、公開状態）
- クエリ最適化（select_related, prefetch_related, only）
- パフォーマンス監視デコレータ
- データベース接続プーリング
- VACUUM ANALYZE自動実行

### Caching Strategy
- 写真数キャッシュ（1時間TTL）
- ユーザー別キャッシュキー
- キャッシュフォールバック機能
- パフォーマンス統計キャッシュ

### Monitoring & Health Checks
- 基本ヘルスチェック（/health/）
- 詳細システム監視（/health/detailed/）
- レディネス・ライブネスチェック
- リソース使用量監視（CPU、メモリ、ディスク）

## Security Considerations

### Authentication & Authorization
- Django標準認証システム + カスタム拡張
- セッションセキュリティ強化（IPアドレス検証）
- Argon2パスワードハッシュ化
- ログイン試行制限（IP別、時間制限）
- セッションハイジャック対策

### File Security
- 包括的ファイル検証（形式、サイズ、内容）
- EXIF データセキュリティチェック
- ファイル名サニタイズ
- 危険な拡張子・パターン検出
- アップロード頻度制限

### Web Security
- CSRF保護（SameSite、HttpOnly）
- XSS防止（入力サニタイズ、CSP）
- セキュリティヘッダー（X-Frame-Options、X-Content-Type-Options等）
- Content Security Policy実装
- Permissions Policy設定

### Input Validation
- HTMLエスケープ処理
- 危険なパターン検出
- フォームバリデーション強化
- SQLインジェクション防止（Django ORM）

## Testing Strategy

### Unit Tests
- モデルのテスト（Photo, User）
- ビューのテスト（認証、CRUD操作）
- フォームバリデーションテスト
- ユーティリティ関数テスト

### Integration Tests
- ファイルアップロードフロー
- ユーザー認証フロー
- 写真表示・編集フロー
- パーミッションテスト

### Frontend Tests
- レスポンシブデザインテスト
- JavaScript機能テスト
- ブラウザ互換性テスト
- アクセシビリティテスト

### Test Data
- ファクトリーパターン（factory_boy）
- テスト用画像ファイル
- モックデータ生成
- テストデータベース分離