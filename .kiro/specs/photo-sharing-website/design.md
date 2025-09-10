# Design Document

## Overview

写真共有WEBサイトは、Django REST frameworkとPostgreSQLを使用したバックエンドと、Tailwind CSSでスタイリングされたフロントエンドを持つWebアプリケーションです。ユーザー認証、ファイルアップロード、画像処理、レスポンシブデザインを統合したモダンなWebアプリケーションとして設計されています。

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
- `photos/` - 写真のアップロード、管理、表示
- `core/` - 共通機能とユーティリティ
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
- `PhotoListView` - 写真一覧表示（ページネーション付き）
- `PhotoDetailView` - 写真詳細表示
- `PhotoUploadView` - 写真アップロード
- `PhotoUpdateView` - 写真情報編集
- `PhotoDeleteView` - 写真削除
- `PublicGalleryView` - 公開写真ギャラリー

**Templates:**
- `photos/photo_list.html`
- `photos/photo_detail.html`
- `photos/photo_upload.html`
- `photos/photo_edit.html`
- `photos/public_gallery.html`

### 3. Core Utilities (core/)

**Utilities:**
- `image_validator.py` - 画像ファイル検証
- `image_processor.py` - サムネイル生成
- `pagination_helper.py` - ページネーション処理

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
- 自動サムネイル生成（Pillow使用）
- 遅延読み込み（Lazy Loading）
- 画像圧縮とWebP対応
- CDN配信準備（静的ファイル）

### Database Optimization
- 適切なインデックス設定
- クエリ最適化（select_related, prefetch_related）
- ページネーション実装
- データベース接続プーリング

### Caching Strategy
- Django Cache Framework
- テンプレートキャッシュ
- 静的ファイルキャッシュ
- Redis準備（将来的な拡張）

## Security Considerations

### Authentication & Authorization
- Django標準認証システム
- セッション管理
- パスワードハッシュ化
- ログイン試行制限

### File Security
- アップロードファイルの検証
- ファイル名のサニタイズ
- 実行可能ファイルの拒否
- ファイルアクセス権限制御

### Web Security
- CSRF保護
- XSS防止
- セキュアヘッダー設定
- HTTPS強制（本番環境）

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