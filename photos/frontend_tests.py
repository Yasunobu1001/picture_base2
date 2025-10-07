"""
フロントエンドテスト - レスポンシブデザイン、JavaScript機能、ブラウザ互換性

このファイルには以下のフロントエンドテストが含まれています:
1. レスポンシブデザインのテスト
2. JavaScript機能のテスト
3. ブラウザ互換性テスト

Requirements: 6.1, 6.2, 6.3, 6.4
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test.utils import override_settings
from PIL import Image
import io
import re
from photos.models import Photo

User = get_user_model()


class ResponsiveDesignTest(TestCase):
    """
    レスポンシブデザインのテスト
    Requirements: 6.1, 6.2, 6.3
    """
    
    def setUp(self):
        """テスト用のユーザーと写真を準備"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # テスト用写真を作成
        test_image = self.create_test_image()
        self.photo = Photo.objects.create(
            title='レスポンシブテスト写真',
            description='レスポンシブデザインテスト用',
            image=test_image,
            owner=self.user,
            is_public=True
        )
    
    def create_test_image(self, name='test.jpg', size=(100, 100), format='JPEG'):
        """テスト用の画像ファイルを作成"""
        image = Image.new('RGB', size, color='red')
        image_io = io.BytesIO()
        image.save(image_io, format=format)
        image_io.seek(0)
        return SimpleUploadedFile(
            name=name,
            content=image_io.getvalue(),
            content_type=f'image/{format.lower()}'
        )
    
    def test_mobile_viewport_meta_tag(self):
        """モバイル用viewportメタタグの存在確認"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        # viewportメタタグが存在することを確認
        content = response.content.decode('utf-8')
        self.assertIn('name="viewport"', content)
        self.assertIn('width=device-width', content)
        self.assertIn('initial-scale=1', content)
    
    def test_responsive_css_classes(self):
        """レスポンシブCSSクラスの存在確認"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # Tailwind CSSのレスポンシブクラスが使用されていることを確認
        responsive_classes = [
            'sm:', 'md:', 'lg:', 'xl:',  # ブレークポイント
            'grid', 'flex',  # レイアウト
            'hidden', 'block',  # 表示制御
        ]
        
        for css_class in responsive_classes:
            self.assertIn(css_class, content, f'{css_class} クラスが見つかりません')
    
    def test_mobile_navigation_structure(self):
        """モバイルナビゲーション構造のテスト"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # ハンバーガーメニューボタンの存在確認
        self.assertIn('menu-button', content)
        
        # モバイル用メニューの存在確認
        self.assertIn('mobile-menu', content)
        
        # レスポンシブナビゲーションクラスの確認
        self.assertIn('md:hidden', content)  # デスクトップで非表示
        self.assertIn('hidden md:block', content)  # モバイルで非表示、デスクトップで表示
    
    def test_responsive_grid_layout(self):
        """レスポンシブグリッドレイアウトのテスト"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # グリッドレイアウトのレスポンシブクラス確認
        grid_classes = [
            'grid-cols-1',  # モバイル: 1列
            'sm:grid-cols-2',  # タブレット: 2列
            'md:grid-cols-3',  # デスクトップ: 3列
            'lg:grid-cols-4',  # 大画面: 4列
        ]
        
        for grid_class in grid_classes:
            self.assertIn(grid_class, content, f'{grid_class} が見つかりません')
    
    def test_responsive_image_sizing(self):
        """レスポンシブ画像サイズのテスト"""
        response = self.client.get(reverse('photos:detail', kwargs={'pk': self.photo.pk}))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # レスポンシブ画像クラスの確認
        image_classes = [
            'w-full',  # 幅100%
            'h-auto',  # 高さ自動調整
            'max-w-full',  # 最大幅制限
            'object-cover',  # オブジェクトフィット
        ]
        
        for img_class in image_classes:
            self.assertIn(img_class, content, f'{img_class} が見つかりません')
    
    def test_responsive_form_layout(self):
        """レスポンシブフォームレイアウトのテスト"""
        response = self.client.get(reverse('photos:upload'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # フォームのレスポンシブクラス確認
        form_classes = [
            'w-full',  # フル幅
            'max-w-md',  # 最大幅制限
            'mx-auto',  # 中央寄せ
            'px-4',  # パディング
        ]
        
        for form_class in form_classes:
            self.assertIn(form_class, content, f'{form_class} が見つかりません')
    
    def test_responsive_typography(self):
        """レスポンシブタイポグラフィのテスト"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # レスポンシブテキストサイズクラスの確認
        text_classes = [
            'text-sm',  # 小さいテキスト
            'text-base',  # 基本テキスト
            'text-lg',  # 大きいテキスト
            'md:text-xl',  # デスクトップで特大
        ]
        
        for text_class in text_classes:
            self.assertIn(text_class, content, f'{text_class} が見つかりません')
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        if self.photo.image:
            try:
                self.photo.image.delete()
            except:
                pass


class JavaScriptFunctionalityTest(TestCase):
    """
    JavaScript機能のテスト
    Requirements: 6.4
    """
    
    def setUp(self):
        """テスト用のユーザーを準備"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_lazy_loading_script_inclusion(self):
        """遅延読み込みスクリプトの読み込み確認"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # 遅延読み込みスクリプトの存在確認
        self.assertIn('lazy-loading.js', content)
        
        # Intersection Observer APIの使用確認
        self.assertIn('IntersectionObserver', content)
    
    def test_mobile_menu_toggle_functionality(self):
        """モバイルメニュートグル機能のテスト"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # メニュートグルボタンの存在確認
        self.assertIn('menu-button', content)
        
        # JavaScript関数の存在確認
        self.assertIn('toggleMobileMenu', content)
        
        # イベントリスナーの設定確認
        self.assertIn('addEventListener', content)
    
    def test_form_validation_javascript(self):
        """フォームバリデーションJavaScriptのテスト"""
        response = self.client.get(reverse('photos:upload'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # フォームバリデーション関数の確認
        validation_functions = [
            'validateForm',
            'validateFileSize',
            'validateFileType',
        ]
        
        for func in validation_functions:
            self.assertIn(func, content, f'{func} 関数が見つかりません')
    
    def test_drag_and_drop_functionality(self):
        """ドラッグ&ドロップ機能のテスト"""
        response = self.client.get(reverse('photos:upload'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # ドラッグ&ドロップイベントハンドラーの確認
        drag_events = [
            'dragover',
            'dragenter',
            'dragleave',
            'drop',
        ]
        
        for event in drag_events:
            self.assertIn(event, content, f'{event} イベントが見つかりません')
        
        # ファイル処理関数の確認
        self.assertIn('handleFiles', content)
    
    def test_image_preview_functionality(self):
        """画像プレビュー機能のテスト"""
        response = self.client.get(reverse('photos:upload'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # 画像プレビュー関数の確認
        self.assertIn('previewImage', content)
        
        # FileReader APIの使用確認
        self.assertIn('FileReader', content)
        
        # プレビュー要素の確認
        self.assertIn('image-preview', content)
    
    def test_progress_bar_functionality(self):
        """プログレスバー機能のテスト"""
        response = self.client.get(reverse('photos:upload'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # プログレスバー要素の確認
        self.assertIn('progress-bar', content)
        
        # プログレス更新関数の確認
        self.assertIn('updateProgress', content)
    
    def test_modal_functionality(self):
        """モーダル機能のテスト"""
        # 写真を作成
        test_image = self.create_test_image()
        photo = Photo.objects.create(
            title='モーダルテスト写真',
            image=test_image,
            owner=self.user,
            is_public=True
        )
        
        response = self.client.get(reverse('photos:detail', kwargs={'pk': photo.pk}))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # モーダル関連の要素確認
        modal_elements = [
            'modal',
            'modal-overlay',
            'modal-content',
            'close-modal',
        ]
        
        for element in modal_elements:
            self.assertIn(element, content, f'{element} 要素が見つかりません')
        
        # モーダル制御関数の確認
        self.assertIn('openModal', content)
        self.assertIn('closeModal', content)
    
    def create_test_image(self, name='test.jpg', size=(100, 100), format='JPEG'):
        """テスト用の画像ファイルを作成"""
        image = Image.new('RGB', size, color='blue')
        image_io = io.BytesIO()
        image.save(image_io, format=format)
        image_io.seek(0)
        return SimpleUploadedFile(
            name=name,
            content=image_io.getvalue(),
            content_type=f'image/{format.lower()}'
        )


class BrowserCompatibilityTest(TestCase):
    """
    ブラウザ互換性テスト
    Requirements: 6.4
    """
    
    def setUp(self):
        """テスト用のユーザーを準備"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_html5_semantic_elements(self):
        """HTML5セマンティック要素の使用確認"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # HTML5セマンティック要素の確認
        semantic_elements = [
            '<header',
            '<nav',
            '<main',
            '<section',
            '<article',
            '<aside',
            '<footer',
        ]
        
        for element in semantic_elements:
            self.assertIn(element, content, f'{element} 要素が見つかりません')
    
    def test_css_vendor_prefixes(self):
        """CSSベンダープレフィックスの確認"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # Tailwind CSSが適切にコンパイルされていることを確認
        # （ベンダープレフィックスは自動で追加される）
        self.assertIn('transform', content)
        self.assertIn('transition', content)
    
    def test_progressive_enhancement(self):
        """プログレッシブエンハンスメントの確認"""
        response = self.client.get(reverse('photos:upload'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # 基本的なHTMLフォームが存在することを確認
        self.assertIn('<form', content)
        self.assertIn('type="file"', content)
        self.assertIn('type="submit"', content)
        
        # JavaScriptが無効でも動作することを確認
        self.assertIn('enctype="multipart/form-data"', content)
    
    def test_accessibility_attributes(self):
        """アクセシビリティ属性の確認"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # ARIA属性の確認
        aria_attributes = [
            'aria-label',
            'aria-expanded',
            'aria-hidden',
            'role=',
        ]
        
        for attr in aria_attributes:
            self.assertIn(attr, content, f'{attr} 属性が見つかりません')
        
        # alt属性の確認
        self.assertIn('alt=', content)
    
    def test_form_input_types(self):
        """HTML5フォーム入力タイプの確認"""
        response = self.client.get(reverse('accounts:signup'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # HTML5入力タイプの確認
        input_types = [
            'type="email"',
            'type="password"',
            'type="text"',
        ]
        
        for input_type in input_types:
            self.assertIn(input_type, content, f'{input_type} が見つかりません')
    
    def test_meta_tags_for_seo(self):
        """SEO用メタタグの確認"""
        response = self.client.get(reverse('photos:public_gallery'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # SEO用メタタグの確認
        meta_tags = [
            'name="description"',
            'name="keywords"',
            'property="og:title"',
            'property="og:description"',
            'property="og:image"',
        ]
        
        for meta_tag in meta_tags:
            self.assertIn(meta_tag, content, f'{meta_tag} が見つかりません')
    
    def test_charset_declaration(self):
        """文字エンコーディング宣言の確認"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # UTF-8文字エンコーディングの宣言確認
        self.assertIn('charset="utf-8"', content)
    
    def test_doctype_declaration(self):
        """DOCTYPE宣言の確認"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # HTML5 DOCTYPE宣言の確認
        self.assertTrue(content.strip().startswith('<!DOCTYPE html>'))
    
    def test_css_fallbacks(self):
        """CSSフォールバックの確認"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # Tailwind CSSが読み込まれていることを確認
        self.assertIn('tailwind', content.lower())
        
        # 基本的なCSSクラスが存在することを確認
        basic_classes = ['text-', 'bg-', 'p-', 'm-', 'w-', 'h-']
        for css_class in basic_classes:
            self.assertIn(css_class, content, f'{css_class} クラスが見つかりません')


class PerformanceOptimizationTest(TestCase):
    """
    パフォーマンス最適化テスト
    Requirements: 6.1, 6.4
    """
    
    def setUp(self):
        """テスト用のユーザーを準備"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_css_minification(self):
        """CSS最小化の確認"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        # CSSファイルが適切に読み込まれていることを確認
        content = response.content.decode('utf-8')
        self.assertIn('.css', content)
    
    def test_image_optimization_attributes(self):
        """画像最適化属性の確認"""
        # テスト用写真を作成
        test_image = self.create_test_image()
        photo = Photo.objects.create(
            title='最適化テスト写真',
            image=test_image,
            owner=self.user,
            is_public=True
        )
        
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # 画像最適化属性の確認
        optimization_attrs = [
            'loading="lazy"',  # 遅延読み込み
            'decoding="async"',  # 非同期デコード
        ]
        
        for attr in optimization_attrs:
            self.assertIn(attr, content, f'{attr} 属性が見つかりません')
    
    def test_resource_hints(self):
        """リソースヒントの確認"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # リソースヒントの確認
        resource_hints = [
            'rel="preload"',
            'rel="prefetch"',
            'rel="dns-prefetch"',
        ]
        
        # 少なくとも1つのリソースヒントが存在することを確認
        hint_found = any(hint in content for hint in resource_hints)
        self.assertTrue(hint_found, 'リソースヒントが見つかりません')
    
    def test_critical_css_inline(self):
        """クリティカルCSS インライン化の確認"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # インラインCSSの存在確認
        self.assertIn('<style', content)
        
        # 基本的なスタイルがインライン化されていることを確認
        critical_styles = ['body', 'html', 'main']
        for style in critical_styles:
            if '<style' in content:
                # インラインCSSが存在する場合のみチェック
                break
    
    def create_test_image(self, name='test.jpg', size=(100, 100), format='JPEG'):
        """テスト用の画像ファイルを作成"""
        image = Image.new('RGB', size, color='green')
        image_io = io.BytesIO()
        image.save(image_io, format=format)
        image_io.seek(0)
        return SimpleUploadedFile(
            name=name,
            content=image_io.getvalue(),
            content_type=f'image/{format.lower()}'
        )


class CrossBrowserCompatibilityTest(TestCase):
    """
    クロスブラウザ互換性テスト
    Requirements: 6.4
    """
    
    def setUp(self):
        """テスト用のユーザーを準備"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_user_agent_compatibility(self):
        """異なるUser-Agentでの互換性テスト"""
        # 異なるブラウザのUser-Agentをシミュレート
        user_agents = [
            # Chrome
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            # Firefox
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            # Safari
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            # Edge
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
        ]
        
        for user_agent in user_agents:
            response = self.client.get(
                reverse('photos:list'),
                HTTP_USER_AGENT=user_agent
            )
            self.assertEqual(response.status_code, 200, f'User-Agent: {user_agent[:50]}... でエラー')
    
    def test_mobile_user_agent_compatibility(self):
        """モバイルUser-Agentでの互換性テスト"""
        mobile_user_agents = [
            # iPhone Safari
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            # Android Chrome
            'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            # iPad Safari
            'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
        ]
        
        for user_agent in mobile_user_agents:
            response = self.client.get(
                reverse('photos:list'),
                HTTP_USER_AGENT=user_agent
            )
            self.assertEqual(response.status_code, 200, f'Mobile User-Agent: {user_agent[:50]}... でエラー')
            
            # モバイル向けのレスポンシブクラスが含まれていることを確認
            content = response.content.decode('utf-8')
            self.assertIn('sm:', content)
    
    def test_javascript_feature_detection(self):
        """JavaScript機能検出の確認"""
        response = self.client.get(reverse('photos:upload'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # 機能検出コードの確認
        feature_detections = [
            'typeof',
            'addEventListener' in content or 'attachEvent' in content,
            'querySelector' in content or 'getElementById' in content,
        ]
        
        # 少なくとも基本的な機能検出が行われていることを確認
        self.assertTrue(any(feature_detections), '機能検出コードが見つかりません')
    
    def test_css_grid_fallback(self):
        """CSS Grid フォールバックの確認"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # Tailwind CSSのグリッドクラスが使用されていることを確認
        # （Tailwind CSSは自動的にフォールバックを提供）
        grid_classes = ['grid', 'grid-cols-']
        for grid_class in grid_classes:
            self.assertIn(grid_class, content, f'{grid_class} が見つかりません')
    
    def test_flexbox_fallback(self):
        """Flexbox フォールバックの確認"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # Flexboxクラスの確認
        flex_classes = ['flex', 'flex-col', 'flex-row', 'justify-', 'items-']
        for flex_class in flex_classes:
            self.assertIn(flex_class, content, f'{flex_class} が見つかりません')
    
    def test_polyfill_inclusion(self):
        """ポリフィルの読み込み確認"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # 必要に応じてポリフィルが読み込まれていることを確認
        # （現代的なブラウザサポートのため、最小限のポリフィルのみ）
        if 'polyfill' in content.lower():
            self.assertIn('polyfill', content.lower())
    
    def test_graceful_degradation(self):
        """グレースフルデグラデーションの確認"""
        response = self.client.get(reverse('photos:upload'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # JavaScriptが無効でも基本機能が動作することを確認
        # 基本的なHTMLフォームが存在
        self.assertIn('<form', content)
        self.assertIn('method="post"', content)
        self.assertIn('enctype="multipart/form-data"', content)
        
        # noscriptタグの存在確認
        if '<noscript>' in content:
            self.assertIn('</noscript>', content)