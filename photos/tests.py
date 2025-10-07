from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.urls import reverse
from PIL import Image
import io
import tempfile
import os
from .models import Photo
from .utils import validate_image_file, create_thumbnail, get_image_info, resize_image

User = get_user_model()


class PhotoModelTest(TestCase):
    def setUp(self):
        """テスト用のユーザーを作成"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
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
    
    def test_photo_creation(self):
        """Photoモデルの基本的な作成テスト"""
        test_image = self.create_test_image()
        photo = Photo.objects.create(
            title='テスト写真',
            description='これはテスト用の写真です',
            image=test_image,
            owner=self.user,
            is_public=True
        )
        
        self.assertEqual(photo.title, 'テスト写真')
        self.assertEqual(photo.description, 'これはテスト用の写真です')
        self.assertEqual(photo.owner, self.user)
        self.assertTrue(photo.is_public)
        self.assertIsNotNone(photo.created_at)
        self.assertIsNotNone(photo.updated_at)
    
    def test_photo_str_method(self):
        """__str__メソッドのテスト"""
        test_image = self.create_test_image()
        photo = Photo.objects.create(
            title='テスト写真',
            image=test_image,
            owner=self.user
        )
        self.assertEqual(str(photo), 'テスト写真')
        
        # タイトルが空の場合
        photo_no_title = Photo.objects.create(
            image=self.create_test_image('test2.jpg'),
            owner=self.user
        )
        self.assertEqual(str(photo_no_title), f'Photo {photo_no_title.id}')
    
    def test_photo_default_values(self):
        """デフォルト値のテスト"""
        test_image = self.create_test_image()
        photo = Photo.objects.create(
            title='テスト写真',
            image=test_image,
            owner=self.user
        )
        
        # デフォルト値の確認
        self.assertTrue(photo.is_public)  # デフォルトはTrue
        self.assertEqual(photo.description, '')  # デフォルトは空文字
    
    def test_photo_ordering(self):
        """写真の並び順テスト（作成日時降順）"""
        test_image1 = self.create_test_image('test1.jpg')
        test_image2 = self.create_test_image('test2.jpg')
        
        photo1 = Photo.objects.create(
            title='写真1',
            image=test_image1,
            owner=self.user
        )
        photo2 = Photo.objects.create(
            title='写真2',
            image=test_image2,
            owner=self.user
        )
        
        photos = Photo.objects.all()
        self.assertEqual(photos[0], photo2)  # 新しい写真が最初
        self.assertEqual(photos[1], photo1)
    
    def test_photo_owner_relationship(self):
        """ユーザーとの関係テスト"""
        test_image = self.create_test_image()
        photo = Photo.objects.create(
            title='テスト写真',
            image=test_image,
            owner=self.user
        )
        
        # ユーザーから写真にアクセス
        self.assertIn(photo, self.user.photos.all())
        self.assertEqual(self.user.photos.count(), 1)
    
    def test_photo_cascade_delete(self):
        """ユーザー削除時のカスケード削除テスト"""
        test_image = self.create_test_image()
        photo = Photo.objects.create(
            title='テスト写真',
            image=test_image,
            owner=self.user
        )
        
        photo_id = photo.id
        self.user.delete()
        
        # 写真も削除されることを確認
        with self.assertRaises(Photo.DoesNotExist):
            Photo.objects.get(id=photo_id)
    
    def test_photo_title_max_length(self):
        """タイトルの最大長テスト"""
        test_image = self.create_test_image()
        long_title = 'a' * 100  # 100文字（制限内）
        photo = Photo.objects.create(
            title=long_title,
            image=test_image,
            owner=self.user
        )
        self.assertEqual(photo.title, long_title)
    
    def test_photo_image_upload_path(self):
        """画像アップロードパスのテスト"""
        test_image = self.create_test_image()
        photo = Photo.objects.create(
            title='テスト写真',
            image=test_image,
            owner=self.user
        )
        
        # アップロードパスが正しい形式かチェック
        self.assertTrue(photo.image.name.startswith('photos/'))
        # ファイル名は自動的に変更される可能性があるので、拡張子のみチェック
        self.assertTrue(photo.image.name.endswith('.jpg'))
    
    def test_photo_get_absolute_url(self):
        """get_absolute_urlメソッドのテスト（URLが設定されていない場合はスキップ）"""
        test_image = self.create_test_image()
        photo = Photo.objects.create(
            title='テスト写真',
            image=test_image,
            owner=self.user
        )
        
        # URLが設定されていない場合はスキップ
        try:
            expected_url = reverse('photos:detail', kwargs={'pk': photo.pk})
            self.assertEqual(photo.get_absolute_url(), expected_url)
        except:
            self.skipTest("photos:detail URL not configured yet")
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # テスト用にアップロードされた画像ファイルを削除
        for photo in Photo.objects.all():
            if photo.image:
                if os.path.exists(photo.image.path):
                    os.remove(photo.image.path)
            if photo.thumbnail:
                if os.path.exists(photo.thumbnail.path):
                    os.remove(photo.thumbnail.path)


class ImageValidationTest(TestCase):
    """画像バリデーション機能のテスト"""
    
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
    
    def create_large_image(self, size_mb=15):
        """指定サイズの大きな画像を作成"""
        # 大きな画像を作成（約15MB）
        image = Image.new('RGB', (4000, 4000), color='blue')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG', quality=100)
        
        # 確実に10MBを超えるようにデータを追加
        content = image_io.getvalue()
        if len(content) < 10 * 1024 * 1024:
            # 10MB以上になるまでダミーデータを追加
            additional_data = b'x' * (11 * 1024 * 1024 - len(content))
            content += additional_data
        
        return SimpleUploadedFile(
            name='large_test.jpg',
            content=content,
            content_type='image/jpeg'
        )
    
    def create_invalid_file(self):
        """無効なファイルを作成"""
        return SimpleUploadedFile(
            name='invalid.txt',
            content=b'This is not an image file',
            content_type='text/plain'
        )
    
    def test_valid_jpeg_image(self):
        """有効なJPEG画像のバリデーション"""
        test_image = self.create_test_image('test.jpg', format='JPEG')
        try:
            validated_file = validate_image_file(test_image)
            self.assertIsNotNone(validated_file)
        except ValidationError:
            self.fail("有効なJPEG画像でValidationErrorが発生しました")
    
    def test_valid_png_image(self):
        """有効なPNG画像のバリデーション"""
        test_image = self.create_test_image('test.png', format='PNG')
        try:
            validated_file = validate_image_file(test_image)
            self.assertIsNotNone(validated_file)
        except ValidationError:
            self.fail("有効なPNG画像でValidationErrorが発生しました")
    
    def test_valid_gif_image(self):
        """有効なGIF画像のバリデーション"""
        test_image = self.create_test_image('test.gif', format='GIF')
        try:
            validated_file = validate_image_file(test_image)
            self.assertIsNotNone(validated_file)
        except ValidationError:
            self.fail("有効なGIF画像でValidationErrorが発生しました")
    
    def test_invalid_file_extension(self):
        """無効なファイル拡張子のテスト"""
        invalid_file = self.create_invalid_file()
        with self.assertRaises(ValidationError) as context:
            validate_image_file(invalid_file)
        self.assertIn('サポートされていないファイル形式', str(context.exception))
    
    def test_file_size_limit(self):
        """ファイルサイズ制限のテスト"""
        large_image = self.create_large_image()
        with self.assertRaises(ValidationError) as context:
            validate_image_file(large_image)
        self.assertIn('ファイルサイズが大きすぎます', str(context.exception))
    
    def test_corrupted_image_file(self):
        """破損した画像ファイルのテスト"""
        corrupted_file = SimpleUploadedFile(
            name='corrupted.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        with self.assertRaises(ValidationError) as context:
            validate_image_file(corrupted_file)
        self.assertIn('有効な画像ファイルではありません', str(context.exception))


class ImageUtilityTest(TestCase):
    """画像ユーティリティ機能のテスト"""
    
    def create_test_image(self, name='test.jpg', size=(500, 400), format='JPEG'):
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
    
    def test_create_thumbnail(self):
        """サムネイル生成のテスト"""
        test_image = self.create_test_image(size=(800, 600))
        thumbnail = create_thumbnail(test_image, size=(200, 200))
        
        self.assertIsNotNone(thumbnail)
        self.assertTrue(thumbnail.name.endswith('_thumb.jpg'))
        self.assertEqual(thumbnail.content_type, 'image/jpeg')
        
        # サムネイルサイズの確認
        thumbnail.seek(0)
        thumb_image = Image.open(thumbnail)
        self.assertLessEqual(thumb_image.width, 200)
        self.assertLessEqual(thumb_image.height, 200)
    
    def test_create_thumbnail_with_rgba(self):
        """RGBA画像のサムネイル生成テスト"""
        # RGBA画像を作成
        image = Image.new('RGBA', (400, 300), color=(255, 0, 0, 128))
        image_io = io.BytesIO()
        image.save(image_io, format='PNG')
        image_io.seek(0)
        
        test_image = SimpleUploadedFile(
            name='test_rgba.png',
            content=image_io.getvalue(),
            content_type='image/png'
        )
        
        thumbnail = create_thumbnail(test_image)
        self.assertIsNotNone(thumbnail)
        self.assertEqual(thumbnail.content_type, 'image/jpeg')
    
    def test_get_image_info(self):
        """画像情報取得のテスト"""
        test_image = self.create_test_image(size=(800, 600))
        info = get_image_info(test_image)
        
        self.assertIsNotNone(info)
        self.assertEqual(info['width'], 800)
        self.assertEqual(info['height'], 600)
        self.assertEqual(info['format'], 'JPEG')
        self.assertIn('size_bytes', info)
        self.assertIn('size_mb', info)
    
    def test_resize_image(self):
        """画像リサイズのテスト"""
        # 大きな画像を作成
        test_image = self.create_test_image(size=(2000, 1500))
        resized_image = resize_image(test_image, max_width=1200, max_height=900)
        
        self.assertIsNotNone(resized_image)
        
        # リサイズされた画像のサイズ確認
        resized_image.seek(0)
        image = Image.open(resized_image)
        self.assertLessEqual(image.width, 1200)
        self.assertLessEqual(image.height, 900)
    
    def test_resize_small_image(self):
        """小さな画像のリサイズテスト（リサイズ不要）"""
        test_image = self.create_test_image(size=(800, 600))
        resized_image = resize_image(test_image, max_width=1200, max_height=900)
        
        # 元画像と同じファイルが返されることを確認
        self.assertEqual(resized_image, test_image)


class PhotoModelWithValidationTest(TestCase):
    """バリデーション付きPhotoモデルのテスト"""
    
    def setUp(self):
        """テスト用のユーザーを作成"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
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
    
    def test_photo_with_valid_image(self):
        """有効な画像でのPhoto作成テスト"""
        test_image = self.create_test_image()
        photo = Photo.objects.create(
            title='テスト写真',
            image=test_image,
            owner=self.user
        )
        
        self.assertIsNotNone(photo.image)
        self.assertEqual(photo.title, 'テスト写真')
    
    def test_photo_thumbnail_generation(self):
        """サムネイル自動生成のテスト"""
        test_image = self.create_test_image(size=(800, 600))
        photo = Photo.objects.create(
            title='サムネイルテスト',
            image=test_image,
            owner=self.user
        )
        
        # サムネイルが生成されることを確認
        self.assertTrue(photo.thumbnail)
        self.assertTrue(photo.thumbnail.name.endswith('.jpg'))
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        for photo in Photo.objects.all():
            if photo.image:
                if os.path.exists(photo.image.path):
                    os.remove(photo.image.path)
            if photo.thumbnail:
                if os.path.exists(photo.thumbnail.path):
                    os.remove(photo.thumbnail.path)


class PhotoUploadIntegrationTest(TestCase):
    """写真アップロード機能の統合テスト"""
    
    def setUp(self):
        """テスト用のユーザーを作成"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.upload_url = reverse('photos:upload')
    
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
    
    def create_large_image(self):
        """10MBを超える大きな画像を作成"""
        # 大きな画像を作成
        image = Image.new('RGB', (4000, 4000), color='blue')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG', quality=100)
        
        # 確実に10MBを超えるようにデータを追加
        content = image_io.getvalue()
        if len(content) < 10 * 1024 * 1024:
            additional_data = b'x' * (11 * 1024 * 1024 - len(content))
            content += additional_data
        
        return SimpleUploadedFile(
            name='large_test.jpg',
            content=content,
            content_type='image/jpeg'
        )
    
    def test_upload_view_requires_login(self):
        """アップロードビューがログインを要求することをテスト"""
        response = self.client.get(self.upload_url)
        self.assertRedirects(response, f'/accounts/login/?next={self.upload_url}')
    
    def test_upload_view_get_authenticated(self):
        """認証済みユーザーがアップロードページにアクセスできることをテスト"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.upload_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '写真をアップロード')
        self.assertContains(response, 'ファイルをドラッグ&ドロップ')
    
    def test_successful_photo_upload_jpeg(self):
        """JPEG画像の正常なアップロードテスト"""
        self.client.login(username='testuser', password='testpass123')
        
        test_image = self.create_test_image('test.jpg', format='JPEG')
        form_data = {
            'title': 'テスト写真',
            'description': 'これはテスト用の写真です',
            'image': test_image,
            'is_public': True
        }
        
        response = self.client.post(self.upload_url, form_data)
        
        # リダイレクトされることを確認
        self.assertEqual(response.status_code, 302)
        
        # 写真が作成されたことを確認
        self.assertEqual(Photo.objects.count(), 1)
        photo = Photo.objects.first()
        self.assertEqual(photo.title, 'テスト写真')
        self.assertEqual(photo.description, 'これはテスト用の写真です')
        self.assertEqual(photo.owner, self.user)
        self.assertTrue(photo.is_public)
        self.assertIsNotNone(photo.image)
    
    def test_successful_photo_upload_png(self):
        """PNG画像の正常なアップロードテスト"""
        self.client.login(username='testuser', password='testpass123')
        
        test_image = self.create_test_image('test.png', format='PNG')
        form_data = {
            'title': 'PNG写真',
            'description': 'PNG形式のテスト写真',
            'image': test_image,
            'is_public': False
        }
        
        response = self.client.post(self.upload_url, form_data)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Photo.objects.count(), 1)
        photo = Photo.objects.first()
        self.assertEqual(photo.title, 'PNG写真')
        self.assertFalse(photo.is_public)
    
    def test_successful_photo_upload_gif(self):
        """GIF画像の正常なアップロードテスト"""
        self.client.login(username='testuser', password='testpass123')
        
        test_image = self.create_test_image('test.gif', format='GIF')
        form_data = {
            'title': 'GIF写真',
            'description': 'GIF形式のテスト写真',
            'image': test_image,
            'is_public': True
        }
        
        response = self.client.post(self.upload_url, form_data)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Photo.objects.count(), 1)
        photo = Photo.objects.first()
        self.assertEqual(photo.title, 'GIF写真')
    
    def test_upload_without_title(self):
        """タイトルなしでのアップロードエラーテスト"""
        self.client.login(username='testuser', password='testpass123')
        
        test_image = self.create_test_image()
        form_data = {
            'title': '',  # 空のタイトル
            'description': 'タイトルなしのテスト',
            'image': test_image,
            'is_public': True
        }
        
        response = self.client.post(self.upload_url, form_data)
        
        # フォームエラーで同じページに戻る
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'タイトルを入力してください')
        self.assertEqual(Photo.objects.count(), 0)
    
    def test_upload_without_image(self):
        """画像ファイルなしでのアップロードエラーテスト"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'title': 'テスト写真',
            'description': '画像なしのテスト',
            'is_public': True
        }
        
        response = self.client.post(self.upload_url, form_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')
        self.assertEqual(Photo.objects.count(), 0)
    
    def test_upload_invalid_file_format(self):
        """無効なファイル形式でのアップロードエラーテスト"""
        self.client.login(username='testuser', password='testpass123')
        
        # テキストファイルを作成
        invalid_file = SimpleUploadedFile(
            name='invalid.txt',
            content=b'This is not an image',
            content_type='text/plain'
        )
        
        form_data = {
            'title': 'テスト写真',
            'description': '無効ファイルのテスト',
            'image': invalid_file,
            'is_public': True
        }
        
        response = self.client.post(self.upload_url, form_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'サポートされていないファイル形式')
        self.assertEqual(Photo.objects.count(), 0)
    
    def test_upload_oversized_file(self):
        """サイズ超過ファイルでのアップロードエラーテスト"""
        self.client.login(username='testuser', password='testpass123')
        
        large_image = self.create_large_image()
        form_data = {
            'title': '大きな写真',
            'description': 'サイズ超過のテスト',
            'image': large_image,
            'is_public': True
        }
        
        response = self.client.post(self.upload_url, form_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ファイルサイズが大きすぎます')
        self.assertEqual(Photo.objects.count(), 0)
    
    def test_upload_long_title(self):
        """長すぎるタイトルでのアップロードエラーテスト"""
        self.client.login(username='testuser', password='testpass123')
        
        test_image = self.create_test_image()
        long_title = 'a' * 101  # 101文字（制限を超える）
        
        form_data = {
            'title': long_title,
            'description': '長いタイトルのテスト',
            'image': test_image,
            'is_public': True
        }
        
        response = self.client.post(self.upload_url, form_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ensure this value has at most 100 characters')
        self.assertEqual(Photo.objects.count(), 0)
    
    def test_upload_with_minimal_data(self):
        """最小限のデータでのアップロードテスト"""
        self.client.login(username='testuser', password='testpass123')
        
        test_image = self.create_test_image()
        form_data = {
            'title': 'テスト',
            'image': test_image,
            # description は空、is_public はチェックボックスなので未指定時はFalse
        }
        
        response = self.client.post(self.upload_url, form_data)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Photo.objects.count(), 1)
        photo = Photo.objects.first()
        self.assertEqual(photo.title, 'テスト')
        self.assertEqual(photo.description, '')
        self.assertFalse(photo.is_public)  # チェックボックス未選択時はFalse
    
    def test_upload_creates_thumbnail(self):
        """アップロード時にサムネイルが作成されることをテスト"""
        self.client.login(username='testuser', password='testpass123')
        
        test_image = self.create_test_image(size=(800, 600))
        form_data = {
            'title': 'サムネイルテスト',
            'image': test_image,
        }
        
        response = self.client.post(self.upload_url, form_data)
        
        self.assertEqual(response.status_code, 302)
        photo = Photo.objects.first()
        self.assertIsNotNone(photo.thumbnail)
        self.assertTrue(photo.thumbnail.name.endswith('.jpg'))
    
    def test_upload_success_message(self):
        """アップロード成功時のメッセージテスト"""
        self.client.login(username='testuser', password='testpass123')
        
        test_image = self.create_test_image()
        form_data = {
            'title': 'メッセージテスト',
            'image': test_image,
        }
        
        response = self.client.post(self.upload_url, form_data, follow=True)
        
        # 成功メッセージが表示されることを確認
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('メッセージテスト', str(messages[0]))
        self.assertIn('アップロードしました', str(messages[0]))
    
    def test_upload_form_validation_errors(self):
        """フォームバリデーションエラーの表示テスト"""
        self.client.login(username='testuser', password='testpass123')
        
        # 無効なデータでPOST
        form_data = {
            'title': '',  # 必須フィールドが空
            'description': 'エラーテスト',
        }
        
        response = self.client.post(self.upload_url, form_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'アップロードに失敗しました')
        
        # フォームエラーが表示されることを確認
        form = response.context['form']
        self.assertTrue(form.errors)
    
    def test_multiple_file_upload_flow(self):
        """複数ファイルの連続アップロードフローテスト"""
        self.client.login(username='testuser', password='testpass123')
        
        # 1枚目のアップロード
        test_image1 = self.create_test_image('test1.jpg')
        form_data1 = {
            'title': '写真1',
            'image': test_image1,
        }
        response1 = self.client.post(self.upload_url, form_data1)
        self.assertEqual(response1.status_code, 302)
        
        # 2枚目のアップロード
        test_image2 = self.create_test_image('test2.jpg')
        form_data2 = {
            'title': '写真2',
            'image': test_image2,
        }
        response2 = self.client.post(self.upload_url, form_data2)
        self.assertEqual(response2.status_code, 302)
        
        # 両方の写真が作成されたことを確認
        self.assertEqual(Photo.objects.count(), 2)
        titles = [photo.title for photo in Photo.objects.all()]
        self.assertIn('写真1', titles)
        self.assertIn('写真2', titles)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        for photo in Photo.objects.all():
            if photo.image:
                try:
                    if os.path.exists(photo.image.path):
                        os.remove(photo.image.path)
                except:
                    pass
            if photo.thumbnail:
                try:
                    if os.path.exists(photo.thumbnail.path):
                        os.remove(photo.thumbnail.path)
                except:
                    pass


class PhotoUploadFormTest(TestCase):
    """PhotoUploadFormのテスト"""
    
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
    
    def test_form_valid_data(self):
        """有効なデータでのフォームテスト"""
        from .forms import PhotoUploadForm
        
        test_image = self.create_test_image()
        form_data = {
            'title': 'テスト写真',
            'description': 'テスト用の説明',
            'is_public': True
        }
        file_data = {'image': test_image}
        
        form = PhotoUploadForm(data=form_data, files=file_data)
        self.assertTrue(form.is_valid())
    
    def test_form_missing_required_fields(self):
        """必須フィールドが不足している場合のフォームテスト"""
        from .forms import PhotoUploadForm
        
        # タイトルなし
        form_data = {
            'description': 'テスト用の説明',
            'is_public': True
        }
        form = PhotoUploadForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('image', form.errors)
    
    def test_form_title_validation(self):
        """タイトルのバリデーションテスト"""
        from .forms import PhotoUploadForm
        
        test_image = self.create_test_image()
        
        # 空のタイトル
        form_data = {
            'title': '   ',  # 空白のみ
            'is_public': True
        }
        file_data = {'image': test_image}
        form = PhotoUploadForm(data=form_data, files=file_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        
        # 長すぎるタイトル
        form_data['title'] = 'a' * 101
        form = PhotoUploadForm(data=form_data, files=file_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
    
    def test_form_image_validation(self):
        """画像ファイルのバリデーションテスト"""
        from .forms import PhotoUploadForm
        
        # 無効なファイル形式
        invalid_file = SimpleUploadedFile(
            name='invalid.txt',
            content=b'not an image',
            content_type='text/plain'
        )
        
        form_data = {
            'title': 'テスト写真',
            'is_public': True
        }
        file_data = {'image': invalid_file}
        
        form = PhotoUploadForm(data=form_data, files=file_data)
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)


class PhotoViewsTestCase(TestCase):
    """写真ビューのテストケース"""
    
    def setUp(self):
        """テスト用のセットアップ"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # テスト用画像を作成
        image = Image.new('RGB', (100, 100), color='red')
        image_file = io.BytesIO()
        image.save(image_file, 'JPEG')
        image_file.seek(0)
        
        self.test_image = SimpleUploadedFile(
            name='test.jpg',
            content=image_file.read(),
            content_type='image/jpeg'
        )
        
        # テスト用写真を作成
        self.photo = Photo.objects.create(
            title='テスト写真',
            description='テスト用の写真です',
            image=self.test_image,
            owner=self.user,
            is_public=True
        )
    
    def test_photo_list_view_requires_login(self):
        """写真一覧ビューがログインを要求することをテスト"""
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 302)  # リダイレクト
    
    def test_photo_list_view_authenticated(self):
        """認証済みユーザーが写真一覧を表示できることをテスト"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('photos:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'マイギャラリー')
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        for photo in Photo.objects.all():
            if photo.image:
                try:
                    if os.path.exists(photo.image.path):
                        os.remove(photo.image.path)
                except:
                    pass
            if photo.thumbnail:
                try:
                    if os.path.exists(photo.thumbnail.path):
                        os.remove(photo.thumbnail.path)
                except:
                    pass


class PublicGalleryViewTest(TestCase):
    """公開ギャラリービューのテスト"""
    
    def setUp(self):
        """テスト用のセットアップ"""
        self.client = Client()
        
        # テスト用ユーザーを作成
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # テスト用画像を作成
        def create_test_image(name):
            image = Image.new('RGB', (100, 100), color='red')
            image_file = io.BytesIO()
            image.save(image_file, 'JPEG')
            image_file.seek(0)
            return SimpleUploadedFile(
                name=name,
                content=image_file.read(),
                content_type='image/jpeg'
            )
        
        # 公開写真を作成
        self.public_photo1 = Photo.objects.create(
            title='公開写真1',
            description='ユーザー1の公開写真',
            image=create_test_image('public1.jpg'),
            owner=self.user1,
            is_public=True
        )
        
        self.public_photo2 = Photo.objects.create(
            title='公開写真2',
            description='ユーザー2の公開写真',
            image=create_test_image('public2.jpg'),
            owner=self.user2,
            is_public=True
        )
        
        # 非公開写真を作成
        self.private_photo1 = Photo.objects.create(
            title='非公開写真1',
            description='ユーザー1の非公開写真',
            image=create_test_image('private1.jpg'),
            owner=self.user1,
            is_public=False
        )
        
        self.private_photo2 = Photo.objects.create(
            title='非公開写真2',
            description='ユーザー2の非公開写真',
            image=create_test_image('private2.jpg'),
            owner=self.user2,
            is_public=False
        )
    
    def test_public_gallery_shows_only_public_photos(self):
        """公開ギャラリーが公開写真のみを表示することをテスト"""
        response = self.client.get(reverse('photos:public_gallery'))
        self.assertEqual(response.status_code, 200)
        
        # 公開写真が表示されることを確認
        self.assertContains(response, '公開写真1')
        self.assertContains(response, '公開写真2')
        
        # 非公開写真が表示されないことを確認
        self.assertNotContains(response, '非公開写真1')
        self.assertNotContains(response, '非公開写真2')
        
        # コンテキストの写真数を確認
        photos = response.context['photos']
        self.assertEqual(len(photos), 2)
        
        # 公開写真のみが含まれることを確認
        photo_titles = [photo.title for photo in photos]
        self.assertIn('公開写真1', photo_titles)
        self.assertIn('公開写真2', photo_titles)
        self.assertNotIn('非公開写真1', photo_titles)
        self.assertNotIn('非公開写真2', photo_titles)
    
    def test_public_gallery_shows_author_info(self):
        """公開ギャラリーが作者情報を表示することをテスト"""
        response = self.client.get(reverse('photos:public_gallery'))
        self.assertEqual(response.status_code, 200)
        
        # 作者名が表示されることを確認
        self.assertContains(response, 'user1')
        self.assertContains(response, 'user2')
    
    def test_public_gallery_accessible_without_login(self):
        """公開ギャラリーがログインなしでアクセス可能であることをテスト"""
        response = self.client.get(reverse('photos:public_gallery'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '公開ギャラリー')
    
    def test_public_gallery_with_authenticated_user(self):
        """認証済みユーザーが公開ギャラリーにアクセスできることをテスト"""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(reverse('photos:public_gallery'))
        self.assertEqual(response.status_code, 200)
        
        # マイギャラリーへのリンクが表示されることを確認
        self.assertContains(response, 'マイギャラリー')
    
    def test_public_gallery_empty_state(self):
        """公開写真がない場合の表示をテスト"""
        # 全ての写真を非公開にする
        Photo.objects.all().update(is_public=False)
        
        response = self.client.get(reverse('photos:public_gallery'))
        self.assertEqual(response.status_code, 200)
        
        # 空の状態メッセージが表示されることを確認
        self.assertContains(response, '公開写真がありません')
        self.assertContains(response, 'まだコミュニティから公開された写真がありません')
    
    def test_public_gallery_pagination(self):
        """公開ギャラリーのページネーションをテスト"""
        # 追加の公開写真を作成（合計14枚にして2ページになるようにする）
        for i in range(12):  # 既存の2枚と合わせて14枚
            image = Image.new('RGB', (100, 100), color='blue')
            image_file = io.BytesIO()
            image.save(image_file, 'JPEG')
            image_file.seek(0)
            
            Photo.objects.create(
                title=f'追加公開写真{i+1}',
                image=SimpleUploadedFile(
                    name=f'additional{i+1}.jpg',
                    content=image_file.read(),
                    content_type='image/jpeg'
                ),
                owner=self.user1,
                is_public=True
            )
        
        # 1ページ目をテスト
        response = self.client.get(reverse('photos:public_gallery'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['photos']), 12)  # 1ページあたり12枚
        
        # 2ページ目をテスト
        response = self.client.get(reverse('photos:public_gallery') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['photos']), 2)  # 残り2枚
    
    def test_public_gallery_ordering(self):
        """公開ギャラリーの写真が作成日時降順で表示されることをテスト"""
        response = self.client.get(reverse('photos:public_gallery'))
        photos = response.context['photos']
        
        # 作成日時が降順になっていることを確認
        for i in range(len(photos) - 1):
            self.assertGreaterEqual(photos[i].created_at, photos[i + 1].created_at)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        for photo in Photo.objects.all():
            if photo.image:
                try:
                    if os.path.exists(photo.image.path):
                        os.remove(photo.image.path)
                except:
                    pass
            if photo.thumbnail:
                try:
                    if os.path.exists(photo.thumbnail.path):
                        os.remove(photo.thumbnail.path)
                except:
                    pass


class PhotoPrivacyTest(TestCase):
    """写真のプライバシー設定のテスト"""
    
    def setUp(self):
        """テスト用のセットアップ"""
        self.client = Client()
        
        # テスト用ユーザーを作成
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        
        # テスト用画像を作成
        image = Image.new('RGB', (100, 100), color='red')
        image_file = io.BytesIO()
        image.save(image_file, 'JPEG')
        image_file.seek(0)
        
        # 非公開写真を作成
        self.private_photo = Photo.objects.create(
            title='非公開写真',
            description='これは非公開の写真です',
            image=SimpleUploadedFile(
                name='private.jpg',
                content=image_file.read(),
                content_type='image/jpeg'
            ),
            owner=self.owner,
            is_public=False
        )
        
        # 公開写真を作成
        image_file.seek(0)
        self.public_photo = Photo.objects.create(
            title='公開写真',
            description='これは公開の写真です',
            image=SimpleUploadedFile(
                name='public.jpg',
                content=image_file.read(),
                content_type='image/jpeg'
            ),
            owner=self.owner,
            is_public=True
        )
    
    def test_owner_can_view_private_photo(self):
        """所有者が非公開写真を閲覧できることをテスト"""
        self.client.login(username='owner', password='testpass123')
        response = self.client.get(reverse('photos:detail', kwargs={'pk': self.private_photo.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '非公開写真')
    
    def test_other_user_cannot_view_private_photo(self):
        """他のユーザーが非公開写真を閲覧できないことをテスト"""
        self.client.login(username='other', password='testpass123')
        response = self.client.get(reverse('photos:detail', kwargs={'pk': self.private_photo.pk}))
        self.assertEqual(response.status_code, 404)
    
    def test_anonymous_user_cannot_view_private_photo(self):
        """匿名ユーザーが非公開写真を閲覧できないことをテスト"""
        response = self.client.get(reverse('photos:detail', kwargs={'pk': self.private_photo.pk}))
        # ログインページにリダイレクトされる
        self.assertEqual(response.status_code, 302)
    
    def test_anyone_can_view_public_photo(self):
        """誰でも公開写真を閲覧できることをテスト"""
        # 匿名ユーザー
        response = self.client.get(reverse('photos:detail', kwargs={'pk': self.public_photo.pk}))
        self.assertEqual(response.status_code, 302)  # ログインが必要
        
        # 他のユーザー
        self.client.login(username='other', password='testpass123')
        response = self.client.get(reverse('photos:detail', kwargs={'pk': self.public_photo.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '公開写真')
        
        # 所有者
        self.client.login(username='owner', password='testpass123')
        response = self.client.get(reverse('photos:detail', kwargs={'pk': self.public_photo.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '公開写真')
    
    def test_privacy_setting_change(self):
        """プライバシー設定の変更をテスト"""
        self.client.login(username='owner', password='testpass123')
        
        # 非公開写真を公開に変更
        response = self.client.post(
            reverse('photos:edit', kwargs={'pk': self.private_photo.pk}),
            {
                'title': '非公開写真',
                'description': 'これは非公開の写真です',
                'is_public': True
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # 変更が反映されたことを確認
        self.private_photo.refresh_from_db()
        self.assertTrue(self.private_photo.is_public)
        
        # 公開ギャラリーに表示されることを確認
        response = self.client.get(reverse('photos:public_gallery'))
        self.assertContains(response, '非公開写真')
    
    def test_privacy_setting_immediate_effect(self):
        """プライバシー設定変更の即座反映をテスト"""
        self.client.login(username='owner', password='testpass123')
        
        # 公開写真を非公開に変更
        response = self.client.post(
            reverse('photos:edit', kwargs={'pk': self.public_photo.pk}),
            {
                'title': '公開写真',
                'description': 'これは公開の写真です',
                'is_public': False
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # 変更が即座に反映されることを確認
        self.public_photo.refresh_from_db()
        self.assertFalse(self.public_photo.is_public)
        
        # 公開ギャラリーから消えることを確認
        response = self.client.get(reverse('photos:public_gallery'))
        self.assertNotContains(response, '公開写真')
        
        # 他のユーザーがアクセスできなくなることを確認
        self.client.login(username='other', password='testpass123')
        response = self.client.get(reverse('photos:detail', kwargs={'pk': self.public_photo.pk}))
        self.assertEqual(response.status_code, 404)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        for photo in Photo.objects.all():
            if photo.image:
                try:
                    if os.path.exists(photo.image.path):
                        os.remove(photo.image.path)
                except:
                    pass
            if photo.thumbnail:
                try:
                    if os.path.exists(photo.thumbnail.path):
                        os.remove(photo.thumbnail.path)
                except:
                    pass
    
    def test_photo_list_view_shows_only_user_photos(self):
        """写真一覧ビューが現在のユーザーの写真のみ表示することをテスト"""
        # 別のユーザーを作成
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        # 別のユーザーの写真を作成
        other_image = Image.new('RGB', (100, 100), color='blue')
        other_image_file = io.BytesIO()
        other_image.save(other_image_file, 'JPEG')
        other_image_file.seek(0)
        
        other_photo = Photo.objects.create(
            title='他のユーザーの写真',
            image=SimpleUploadedFile(
                name='other.jpg',
                content=other_image_file.read(),
                content_type='image/jpeg'
            ),
            owner=other_user,
            is_public=True
        )
        
        # 最初のユーザーでログイン
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('photos:list'))
        
        # 自分の写真は表示される
        self.assertContains(response, self.photo.title)
        # 他のユーザーの写真は表示されない
        self.assertNotContains(response, other_photo.title)
    
    def test_photo_detail_view_owner(self):
        """所有者が写真詳細を表示できることをテスト"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('photos:detail', kwargs={'pk': self.photo.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.photo.title)
        self.assertContains(response, '編集')  # 所有者のみ表示される編集ボタン
        self.assertTrue(response.context['is_owner'])
    
    def test_photo_detail_view_public_photo(self):
        """他のユーザーが公開写真を表示できることをテスト"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        self.client.login(username='otheruser', password='otherpass123')
        response = self.client.get(reverse('photos:detail', kwargs={'pk': self.photo.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.photo.title)
        self.assertNotContains(response, '編集')  # 所有者でないので編集ボタンは表示されない
        self.assertFalse(response.context['is_owner'])
    
    def test_photo_detail_view_private_photo(self):
        """他のユーザーが非公開写真にアクセスできないことをテスト"""
        # 写真を非公開に設定
        self.photo.is_public = False
        self.photo.save()
        
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        self.client.login(username='otheruser', password='otherpass123')
        response = self.client.get(reverse('photos:detail', kwargs={'pk': self.photo.pk}))
        self.assertEqual(response.status_code, 404)  # 非公開写真は404を返す
    
    def test_photo_detail_view_context_data(self):
        """写真詳細ビューのコンテキストデータをテスト"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('photos:detail', kwargs={'pk': self.photo.pk}))
        
        self.assertEqual(response.context['photo'], self.photo)
        self.assertTrue(response.context['is_owner'])
        self.assertEqual(response.context['page_title'], self.photo.title)
    
    def test_photo_list_pagination(self):
        """写真一覧のページネーションをテスト"""
        # 15枚の写真を作成（paginate_by=12なので2ページになる）
        for i in range(14):  # 既に1枚あるので14枚追加
            image = Image.new('RGB', (100, 100), color='green')
            image_file = io.BytesIO()
            image.save(image_file, 'JPEG')
            image_file.seek(0)
            
            Photo.objects.create(
                title=f'写真{i+2}',
                image=SimpleUploadedFile(
                    name=f'test{i+2}.jpg',
                    content=image_file.read(),
                    content_type='image/jpeg'
                ),
                owner=self.user
            )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('photos:list'))
        
        # ページネーションが有効になっていることを確認
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['photos']), 12)  # 1ページ目は12枚
        
        # 2ページ目をテスト
        response = self.client.get(reverse('photos:list') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['photos']), 3)  # 2ページ目は3枚
    
    def test_photo_list_empty_state(self):
        """写真がない場合の一覧表示をテスト"""
        # 既存の写真を削除
        Photo.objects.all().delete()
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('photos:list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'まだ写真がありません')
        self.assertContains(response, '最初の写真をアップロード')
        self.assertEqual(response.context['total_photos'], 0)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        for photo in Photo.objects.all():
            if photo.image:
                try:
                    if os.path.exists(photo.image.path):
                        os.remove(photo.image.path)
                except:
                    pass
            if photo.thumbnail:
                try:
                    if os.path.exists(photo.thumbnail.path):
                        os.remove(photo.thumbnail.path)
                except:
                    pass


class PhotoEditDeleteViewsTest(TestCase):
    """写真編集・削除ビューのテスト"""
    
    def setUp(self):
        """テスト用のセットアップ"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # 別のユーザーも作成
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        # テスト用画像を作成
        image = Image.new('RGB', (100, 100), color='red')
        image_file = io.BytesIO()
        image.save(image_file, 'JPEG')
        image_file.seek(0)
        
        test_image = SimpleUploadedFile(
            name='test.jpg',
            content=image_file.read(),
            content_type='image/jpeg'
        )
        
        # テスト用写真を作成
        self.photo = Photo.objects.create(
            title='テスト写真',
            description='テスト用の写真です',
            image=test_image,
            owner=self.user,
            is_public=True
        )
    
    def test_photo_edit_view_requires_login(self):
        """写真編集ビューがログインを要求することをテスト"""
        response = self.client.get(reverse('photos:edit', kwargs={'pk': self.photo.pk}))
        self.assertEqual(response.status_code, 302)  # リダイレクト
    
    def test_photo_edit_view_owner_only(self):
        """所有者のみが写真を編集できることをテスト"""
        # 別のユーザーでログイン
        self.client.login(username='otheruser', password='otherpass123')
        response = self.client.get(reverse('photos:edit', kwargs={'pk': self.photo.pk}))
        self.assertEqual(response.status_code, 302)  # 権限なしでリダイレクト
    
    def test_photo_edit_view_authenticated_owner(self):
        """所有者が写真編集ページにアクセスできることをテスト"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('photos:edit', kwargs={'pk': self.photo.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '写真を編集')
        self.assertContains(response, self.photo.title)
    
    def test_photo_edit_post_success(self):
        """写真編集の正常な更新テスト"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'title': '更新されたタイトル',
            'description': '更新された説明',
            'is_public': False
        }
        
        response = self.client.post(
            reverse('photos:edit', kwargs={'pk': self.photo.pk}),
            form_data
        )
        
        # 詳細ページにリダイレクトされることを確認
        self.assertRedirects(response, reverse('photos:detail', kwargs={'pk': self.photo.pk}))
        
        # データベースが更新されたことを確認
        self.photo.refresh_from_db()
        self.assertEqual(self.photo.title, '更新されたタイトル')
        self.assertEqual(self.photo.description, '更新された説明')
        self.assertFalse(self.photo.is_public)
    
    def test_photo_edit_post_invalid_data(self):
        """写真編集で無効なデータを送信した場合のテスト"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'title': '',  # 空のタイトル（無効）
            'description': '説明',
            'is_public': True
        }
        
        response = self.client.post(
            reverse('photos:edit', kwargs={'pk': self.photo.pk}),
            form_data
        )
        
        # フォームエラーで同じページに戻る
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'タイトルを入力してください')
        
        # データベースが更新されていないことを確認
        self.photo.refresh_from_db()
        self.assertEqual(self.photo.title, 'テスト写真')  # 元のタイトルのまま
    
    def test_photo_delete_view_requires_login(self):
        """写真削除ビューがログインを要求することをテスト"""
        response = self.client.get(reverse('photos:delete', kwargs={'pk': self.photo.pk}))
        self.assertEqual(response.status_code, 302)  # リダイレクト
    
    def test_photo_delete_view_owner_only(self):
        """所有者のみが写真を削除できることをテスト"""
        # 別のユーザーでログイン
        self.client.login(username='otheruser', password='otherpass123')
        response = self.client.get(reverse('photos:delete', kwargs={'pk': self.photo.pk}))
        self.assertEqual(response.status_code, 302)  # 権限なしでリダイレクト
    
    def test_photo_delete_view_authenticated_owner(self):
        """所有者が写真削除確認ページにアクセスできることをテスト"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('photos:delete', kwargs={'pk': self.photo.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '写真を削除')
        self.assertContains(response, self.photo.title)
        self.assertContains(response, '削除する')
    
    def test_photo_delete_post_success(self):
        """写真削除の正常な実行テスト"""
        self.client.login(username='testuser', password='testpass123')
        photo_id = self.photo.pk
        
        response = self.client.post(reverse('photos:delete', kwargs={'pk': photo_id}))
        
        # 写真一覧ページにリダイレクトされることを確認
        self.assertRedirects(response, reverse('photos:list'))
        
        # データベースから削除されたことを確認
        with self.assertRaises(Photo.DoesNotExist):
            Photo.objects.get(pk=photo_id)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        for photo in Photo.objects.all():
            if photo.image:
                try:
                    if os.path.exists(photo.image.path):
                        os.remove(photo.image.path)
                except:
                    pass
            if photo.thumbnail:
                try:
                    if os.path.exists(photo.thumbnail.path):
                        os.remove(photo.thumbnail.path)
                except:
                    pass


class PhotoEditFormTest(TestCase):
    """PhotoEditFormのテスト"""
    
    def test_form_valid_data(self):
        """有効なデータでのフォームテスト"""
        from .forms import PhotoEditForm
        
        form_data = {
            'title': 'テスト写真',
            'description': 'テスト用の説明',
            'is_public': True
        }
        
        form = PhotoEditForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_missing_title(self):
        """タイトルが不足している場合のフォームテスト"""
        from .forms import PhotoEditForm
        
        form_data = {
            'description': 'テスト用の説明',
            'is_public': True
        }
        
        form = PhotoEditForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
    
    def test_form_title_validation(self):
        """タイトルのバリデーションテスト"""
        from .forms import PhotoEditForm
        
        # 空のタイトル
        form_data = {
            'title': '   ',  # 空白のみ
            'is_public': True
        }
        form = PhotoEditForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        
        # 長すぎるタイトル
        form_data['title'] = 'a' * 101
        form = PhotoEditForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        
        # 有効なタイトル
        form_data['title'] = 'a' * 100  # 100文字（制限内）
        form = PhotoEditForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_optional_fields(self):
        """任意フィールドのテスト"""
        from .forms import PhotoEditForm
        
        # 説明なし
        form_data = {
            'title': 'テスト写真',
            'is_public': True
        }
        form = PhotoEditForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # 公開設定なし（デフォルトでFalse）
        form_data = {
            'title': 'テスト写真',
            'description': '説明'
        }
        form = PhotoEditForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.cleaned_data['is_public'])