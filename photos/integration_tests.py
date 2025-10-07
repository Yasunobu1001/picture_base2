"""
統合テスト - 写真共有サイトの完全なユーザーフロー

このファイルには以下の統合テストが含まれています:
1. ユーザー登録からログイン、写真アップロードまでの完全フロー
2. 写真表示、編集、削除の統合テスト
3. 公開/非公開設定の統合テスト

Requirements: 1.1, 2.1, 3.1, 4.1, 5.1
"""
from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.messages import get_messages
from django.db import transaction
from PIL import Image
import io
import os
import tempfile
from photos.models import Photo

User = get_user_model()


class UserRegistrationToPhotoUploadIntegrationTest(TransactionTestCase):
    """
    ユーザー登録からログイン、写真アップロードまでの完全フロー統合テスト
    Requirements: 1.1, 2.1
    """
    
    def setUp(self):
        """テスト用のクライアントを準備"""
        self.client = Client()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
    
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
    
    def test_complete_user_registration_to_photo_upload_flow(self):
        """
        完全なユーザーフロー: 登録 → ログイン → 写真アップロード → 表示
        """
        # Step 1: ユーザー登録
        signup_response = self.client.post(
            reverse('accounts:signup'), 
            data=self.user_data
        )
        
        # 登録成功後、ログインページにリダイレクトされることを確認
        self.assertEqual(signup_response.status_code, 302)
        self.assertRedirects(signup_response, reverse('accounts:login'))
        
        # ユーザーが作成されたことを確認
        self.assertTrue(User.objects.filter(username='testuser').exists())
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
        
        # Step 2: ログイン
        login_response = self.client.post(
            reverse('accounts:login'),
            data={
                'username': 'testuser',
                'password': 'testpass123'
            }
        )
        
        # ログイン成功後、ホームページにリダイレクトされることを確認
        self.assertEqual(login_response.status_code, 302)
        
        # ユーザーがログインしていることを確認
        user = User.objects.get(username='testuser')
        self.assertTrue('_auth_user_id' in self.client.session)
        
        # Step 3: 写真アップロードページにアクセス
        upload_page_response = self.client.get(reverse('photos:upload'))
        self.assertEqual(upload_page_response.status_code, 200)
        self.assertContains(upload_page_response, '写真をアップロード')
        
        # Step 4: 写真をアップロード
        test_image = self.create_test_image()
        upload_data = {
            'title': '初回アップロード写真',
            'description': 'ユーザー登録後の初回アップロードテスト',
            'image': test_image,
            'is_public': True
        }
        
        upload_response = self.client.post(
            reverse('photos:upload'),
            data=upload_data
        )
        
        # アップロード成功後、写真一覧にリダイレクトされることを確認
        self.assertEqual(upload_response.status_code, 302)
        self.assertRedirects(upload_response, reverse('photos:list'))
        
        # 写真が作成されたことを確認
        self.assertEqual(Photo.objects.count(), 1)
        photo = Photo.objects.first()
        self.assertEqual(photo.title, '初回アップロード写真')
        self.assertEqual(photo.owner, user)
        self.assertTrue(photo.is_public)
        
        # Step 5: 写真一覧ページで写真が表示されることを確認
        list_response = self.client.get(reverse('photos:list'))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, '初回アップロード写真')
        self.assertContains(list_response, 'ユーザー登録後の初回アップロードテスト')
        
        # Step 6: 写真詳細ページにアクセス
        detail_response = self.client.get(
            reverse('photos:detail', kwargs={'pk': photo.pk})
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, '初回アップロード写真')
        self.assertContains(detail_response, 'ユーザー登録後の初回アップロードテスト')
        
        # 所有者として編集・削除ボタンが表示されることを確認
        self.assertContains(detail_response, '編集')
        self.assertContains(detail_response, '削除')
        
        # Step 7: 公開ギャラリーで写真が表示されることを確認
        public_gallery_response = self.client.get(reverse('photos:public_gallery'))
        self.assertEqual(public_gallery_response.status_code, 200)
        self.assertContains(public_gallery_response, '初回アップロード写真')
    
    def test_user_registration_with_invalid_data(self):
        """
        無効なデータでのユーザー登録フロー
        """
        # パスワード不一致での登録試行
        invalid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'differentpass'
        }
        
        response = self.client.post(reverse('accounts:signup'), data=invalid_data)
        
        # フォームエラーで同じページに戻る
        self.assertEqual(response.status_code, 200)
        
        # ユーザーが作成されていないことを確認
        self.assertFalse(User.objects.filter(username='testuser').exists())
        
        # エラーメッセージが表示されることを確認
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('アカウント作成に失敗しました' in str(message) for message in messages))
    
    def test_login_with_invalid_credentials(self):
        """
        無効な認証情報でのログインフロー
        """
        # まずユーザーを作成
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # 間違ったパスワードでログイン試行
        response = self.client.post(
            reverse('accounts:login'),
            data={
                'username': 'testuser',
                'password': 'wrongpassword'
            }
        )
        
        # フォームエラーで同じページに戻る
        self.assertEqual(response.status_code, 200)
        
        # ログインしていないことを確認
        self.assertNotIn('_auth_user_id', self.client.session)
        
        # エラーメッセージが表示されることを確認
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('正しくありません' in str(message) for message in messages))
    
    def test_photo_upload_without_login(self):
        """
        ログインなしでの写真アップロード試行
        """
        # ログインせずにアップロードページにアクセス
        response = self.client.get(reverse('photos:upload'))
        
        # ログインページにリダイレクトされることを確認
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # アップロードされたファイルを削除
        for photo in Photo.objects.all():
            if photo.image and os.path.exists(photo.image.path):
                os.remove(photo.image.path)
            if photo.thumbnail and os.path.exists(photo.thumbnail.path):
                os.remove(photo.thumbnail.path)


class PhotoManagementIntegrationTest(TransactionTestCase):
    """
    写真表示、編集、削除の統合テスト
    Requirements: 3.1, 4.1
    """
    
    def setUp(self):
        """テスト用のユーザーと写真を準備"""
        self.client = Client()
        
        # テストユーザーを作成
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
        
        # ログイン
        self.client.login(username='testuser', password='testpass123')
        
        # テスト用写真を作成
        test_image = self.create_test_image()
        self.photo = Photo.objects.create(
            title='テスト写真',
            description='テスト用の写真です',
            image=test_image,
            owner=self.user,
            is_public=True
        )
    
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
    
    def test_complete_photo_management_flow(self):
        """
        完全な写真管理フロー: 表示 → 編集 → 削除
        """
        # Step 1: 写真一覧で写真が表示されることを確認
        list_response = self.client.get(reverse('photos:list'))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, 'テスト写真')
        
        # Step 2: 写真詳細ページにアクセス
        detail_response = self.client.get(
            reverse('photos:detail', kwargs={'pk': self.photo.pk})
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'テスト写真')
        self.assertContains(detail_response, 'テスト用の写真です')
        
        # 所有者として編集・削除ボタンが表示されることを確認
        self.assertContains(detail_response, '編集')
        self.assertContains(detail_response, '削除')
        
        # Step 3: 写真編集ページにアクセス
        edit_response = self.client.get(
            reverse('photos:edit', kwargs={'pk': self.photo.pk})
        )
        self.assertEqual(edit_response.status_code, 200)
        self.assertContains(edit_response, 'テスト写真')
        
        # Step 4: 写真情報を編集
        edit_data = {
            'title': '編集済み写真',
            'description': '編集後の説明文',
            'is_public': False  # 非公開に変更
        }
        
        edit_post_response = self.client.post(
            reverse('photos:edit', kwargs={'pk': self.photo.pk}),
            data=edit_data
        )
        
        # 編集成功後、詳細ページにリダイレクトされることを確認
        self.assertEqual(edit_post_response.status_code, 302)
        self.assertRedirects(
            edit_post_response, 
            reverse('photos:detail', kwargs={'pk': self.photo.pk})
        )
        
        # 写真情報が更新されたことを確認
        updated_photo = Photo.objects.get(pk=self.photo.pk)
        self.assertEqual(updated_photo.title, '編集済み写真')
        self.assertEqual(updated_photo.description, '編集後の説明文')
        self.assertFalse(updated_photo.is_public)
        
        # Step 5: 編集後の詳細ページで変更が反映されていることを確認
        updated_detail_response = self.client.get(
            reverse('photos:detail', kwargs={'pk': self.photo.pk})
        )
        self.assertEqual(updated_detail_response.status_code, 200)
        self.assertContains(updated_detail_response, '編集済み写真')
        self.assertContains(updated_detail_response, '編集後の説明文')
        
        # Step 6: 公開ギャラリーで非公開写真が表示されないことを確認
        public_gallery_response = self.client.get(reverse('photos:public_gallery'))
        self.assertEqual(public_gallery_response.status_code, 200)
        self.assertNotContains(public_gallery_response, '編集済み写真')
        
        # Step 7: 写真削除ページにアクセス
        delete_response = self.client.get(
            reverse('photos:delete', kwargs={'pk': self.photo.pk})
        )
        self.assertEqual(delete_response.status_code, 200)
        self.assertContains(delete_response, '編集済み写真')
        self.assertContains(delete_response, '削除しますか')
        
        # Step 8: 写真を削除
        delete_post_response = self.client.post(
            reverse('photos:delete', kwargs={'pk': self.photo.pk})
        )
        
        # 削除成功後、写真一覧にリダイレクトされることを確認
        self.assertEqual(delete_post_response.status_code, 302)
        self.assertRedirects(delete_post_response, reverse('photos:list'))
        
        # 写真が削除されたことを確認
        self.assertFalse(Photo.objects.filter(pk=self.photo.pk).exists())
        
        # Step 9: 写真一覧で削除された写真が表示されないことを確認
        final_list_response = self.client.get(reverse('photos:list'))
        self.assertEqual(final_list_response.status_code, 200)
        self.assertNotContains(final_list_response, '編集済み写真')
    
    def test_unauthorized_photo_access(self):
        """
        他のユーザーの写真への不正アクセステスト
        """
        # 他のユーザーでログイン
        self.client.login(username='otheruser', password='otherpass123')
        
        # 他のユーザーの写真編集ページにアクセス試行
        edit_response = self.client.get(
            reverse('photos:edit', kwargs={'pk': self.photo.pk})
        )
        
        # 権限エラーでリダイレクトされることを確認
        self.assertEqual(edit_response.status_code, 302)
        
        # 他のユーザーの写真削除ページにアクセス試行
        delete_response = self.client.get(
            reverse('photos:delete', kwargs={'pk': self.photo.pk})
        )
        
        # 権限エラーでリダイレクトされることを確認
        self.assertEqual(delete_response.status_code, 302)
    
    def test_multiple_photos_management(self):
        """
        複数写真の管理フロー
        """
        # 追加の写真をアップロード
        for i in range(3):
            test_image = self.create_test_image(f'test{i}.jpg')
            Photo.objects.create(
                title=f'写真{i+1}',
                description=f'写真{i+1}の説明',
                image=test_image,
                owner=self.user,
                is_public=True
            )
        
        # 写真一覧で全ての写真が表示されることを確認
        list_response = self.client.get(reverse('photos:list'))
        self.assertEqual(list_response.status_code, 200)
        
        # 元の写真 + 3枚の追加写真 = 4枚
        photos = list_response.context['photos']
        self.assertEqual(len(photos), 4)
        
        # 各写真のタイトルが表示されることを確認
        for i in range(1, 4):
            self.assertContains(list_response, f'写真{i}')
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # アップロードされたファイルを削除
        for photo in Photo.objects.all():
            if photo.image and os.path.exists(photo.image.path):
                os.remove(photo.image.path)
            if photo.thumbnail and os.path.exists(photo.thumbnail.path):
                os.remove(photo.thumbnail.path)


class PhotoPrivacyIntegrationTest(TransactionTestCase):
    """
    公開/非公開設定の統合テスト
    Requirements: 5.1
    """
    
    def setUp(self):
        """テスト用のユーザーと写真を準備"""
        self.client = Client()
        
        # テストユーザーを作成
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
        
        # 各ユーザーの写真を作成
        self.public_photo = Photo.objects.create(
            title='公開写真',
            description='誰でも見ることができる写真',
            image=self.create_test_image('public.jpg'),
            owner=self.user1,
            is_public=True
        )
        
        self.private_photo = Photo.objects.create(
            title='非公開写真',
            description='所有者のみが見ることができる写真',
            image=self.create_test_image('private.jpg'),
            owner=self.user1,
            is_public=False
        )
    
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
    
    def test_public_photo_visibility_flow(self):
        """
        公開写真の可視性フロー
        """
        # Step 1: 所有者としてログイン
        self.client.login(username='user1', password='testpass123')
        
        # 所有者のギャラリーで両方の写真が表示されることを確認
        owner_list_response = self.client.get(reverse('photos:list'))
        self.assertEqual(owner_list_response.status_code, 200)
        self.assertContains(owner_list_response, '公開写真')
        self.assertContains(owner_list_response, '非公開写真')
        
        # Step 2: 公開ギャラリーで公開写真のみが表示されることを確認
        public_gallery_response = self.client.get(reverse('photos:public_gallery'))
        self.assertEqual(public_gallery_response.status_code, 200)
        self.assertContains(public_gallery_response, '公開写真')
        self.assertNotContains(public_gallery_response, '非公開写真')
        
        # Step 3: 他のユーザーでログイン
        self.client.login(username='user2', password='testpass123')
        
        # 他のユーザーの公開写真詳細にアクセス可能
        public_detail_response = self.client.get(
            reverse('photos:detail', kwargs={'pk': self.public_photo.pk})
        )
        self.assertEqual(public_detail_response.status_code, 200)
        self.assertContains(public_detail_response, '公開写真')
        
        # 編集・削除ボタンが表示されないことを確認
        self.assertNotContains(public_detail_response, '編集')
        self.assertNotContains(public_detail_response, '削除')
        
        # Step 4: 他のユーザーが非公開写真にアクセス試行
        private_detail_response = self.client.get(
            reverse('photos:detail', kwargs={'pk': self.private_photo.pk})
        )
        
        # 404エラーが返されることを確認
        self.assertEqual(private_detail_response.status_code, 404)
    
    def test_privacy_setting_change_flow(self):
        """
        プライバシー設定変更フロー
        """
        # 所有者としてログイン
        self.client.login(username='user1', password='testpass123')
        
        # Step 1: 公開写真を非公開に変更
        edit_data = {
            'title': '公開写真',
            'description': '誰でも見ることができる写真',
            'is_public': False  # 非公開に変更
        }
        
        edit_response = self.client.post(
            reverse('photos:edit', kwargs={'pk': self.public_photo.pk}),
            data=edit_data
        )
        
        self.assertEqual(edit_response.status_code, 302)
        
        # 写真が非公開に変更されたことを確認
        updated_photo = Photo.objects.get(pk=self.public_photo.pk)
        self.assertFalse(updated_photo.is_public)
        
        # Step 2: 公開ギャラリーで写真が表示されなくなることを確認
        public_gallery_response = self.client.get(reverse('photos:public_gallery'))
        self.assertEqual(public_gallery_response.status_code, 200)
        self.assertNotContains(public_gallery_response, '公開写真')
        
        # Step 3: 他のユーザーでログイン
        self.client.login(username='user2', password='testpass123')
        
        # 他のユーザーがアクセスできなくなることを確認
        detail_response = self.client.get(
            reverse('photos:detail', kwargs={'pk': self.public_photo.pk})
        )
        self.assertEqual(detail_response.status_code, 404)
        
        # Step 4: 所有者に戻って非公開写真を公開に変更
        self.client.login(username='user1', password='testpass123')
        
        edit_data = {
            'title': '非公開写真',
            'description': '所有者のみが見ることができる写真',
            'is_public': True  # 公開に変更
        }
        
        edit_response = self.client.post(
            reverse('photos:edit', kwargs={'pk': self.private_photo.pk}),
            data=edit_data
        )
        
        self.assertEqual(edit_response.status_code, 302)
        
        # 写真が公開に変更されたことを確認
        updated_photo = Photo.objects.get(pk=self.private_photo.pk)
        self.assertTrue(updated_photo.is_public)
        
        # Step 5: 公開ギャラリーで写真が表示されることを確認
        public_gallery_response = self.client.get(reverse('photos:public_gallery'))
        self.assertEqual(public_gallery_response.status_code, 200)
        self.assertContains(public_gallery_response, '非公開写真')
    
    def test_anonymous_user_access(self):
        """
        匿名ユーザーのアクセステスト
        """
        # ログアウト状態で公開ギャラリーにアクセス
        public_gallery_response = self.client.get(reverse('photos:public_gallery'))
        self.assertEqual(public_gallery_response.status_code, 200)
        self.assertContains(public_gallery_response, '公開写真')
        self.assertNotContains(public_gallery_response, '非公開写真')
        
        # 匿名ユーザーが公開写真詳細にアクセス可能
        public_detail_response = self.client.get(
            reverse('photos:detail', kwargs={'pk': self.public_photo.pk})
        )
        self.assertEqual(public_detail_response.status_code, 200)
        self.assertContains(public_detail_response, '公開写真')
        
        # 編集・削除ボタンが表示されないことを確認
        self.assertNotContains(public_detail_response, '編集')
        self.assertNotContains(public_detail_response, '削除')
        
        # 匿名ユーザーが非公開写真にアクセス試行
        private_detail_response = self.client.get(
            reverse('photos:detail', kwargs={'pk': self.private_photo.pk})
        )
        
        # ログインページにリダイレクトされることを確認
        self.assertEqual(private_detail_response.status_code, 302)
        self.assertIn('/accounts/login/', private_detail_response.url)
    
    def test_bulk_privacy_operations(self):
        """
        一括プライバシー操作のテスト
        """
        # 所有者としてログイン
        self.client.login(username='user1', password='testpass123')
        
        # 複数の写真を作成
        photos = []
        for i in range(5):
            photo = Photo.objects.create(
                title=f'バッチ写真{i+1}',
                description=f'バッチテスト用写真{i+1}',
                image=self.create_test_image(f'batch{i+1}.jpg'),
                owner=self.user1,
                is_public=True
            )
            photos.append(photo)
        
        # 全ての写真が公開ギャラリーに表示されることを確認
        public_gallery_response = self.client.get(reverse('photos:public_gallery'))
        self.assertEqual(public_gallery_response.status_code, 200)
        
        for i in range(5):
            self.assertContains(public_gallery_response, f'バッチ写真{i+1}')
        
        # 各写真を非公開に変更
        for i, photo in enumerate(photos):
            edit_data = {
                'title': f'バッチ写真{i+1}',
                'description': f'バッチテスト用写真{i+1}',
                'is_public': False
            }
            
            edit_response = self.client.post(
                reverse('photos:edit', kwargs={'pk': photo.pk}),
                data=edit_data
            )
            self.assertEqual(edit_response.status_code, 302)
        
        # 公開ギャラリーで全ての写真が表示されなくなることを確認
        updated_public_gallery_response = self.client.get(reverse('photos:public_gallery'))
        self.assertEqual(updated_public_gallery_response.status_code, 200)
        
        for i in range(5):
            self.assertNotContains(updated_public_gallery_response, f'バッチ写真{i+1}')
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # アップロードされたファイルを削除
        for photo in Photo.objects.all():
            if photo.image and os.path.exists(photo.image.path):
                os.remove(photo.image.path)
            if photo.thumbnail and os.path.exists(photo.thumbnail.path):
                os.remove(photo.thumbnail.path)


class CrossUserInteractionIntegrationTest(TransactionTestCase):
    """
    複数ユーザー間の相互作用統合テスト
    Requirements: 1.1, 3.1, 5.1
    """
    
    def setUp(self):
        """テスト用の複数ユーザーと写真を準備"""
        self.client = Client()
        
        # 複数のテストユーザーを作成
        self.users = []
        for i in range(3):
            user = User.objects.create_user(
                username=f'user{i+1}',
                email=f'user{i+1}@example.com',
                password='testpass123'
            )
            self.users.append(user)
        
        # 各ユーザーが写真をアップロード
        self.photos = []
        for i, user in enumerate(self.users):
            # 公開写真
            public_photo = Photo.objects.create(
                title=f'ユーザー{i+1}の公開写真',
                description=f'ユーザー{i+1}がアップロードした公開写真',
                image=self.create_test_image(f'user{i+1}_public.jpg'),
                owner=user,
                is_public=True
            )
            
            # 非公開写真
            private_photo = Photo.objects.create(
                title=f'ユーザー{i+1}の非公開写真',
                description=f'ユーザー{i+1}がアップロードした非公開写真',
                image=self.create_test_image(f'user{i+1}_private.jpg'),
                owner=user,
                is_public=False
            )
            
            self.photos.extend([public_photo, private_photo])
    
    def create_test_image(self, name='test.jpg', size=(100, 100), format='JPEG'):
        """テスト用の画像ファイルを作成"""
        image = Image.new('RGB', size, color='purple')
        image_io = io.BytesIO()
        image.save(image_io, format=format)
        image_io.seek(0)
        return SimpleUploadedFile(
            name=name,
            content=image_io.getvalue(),
            content_type=f'image/{format.lower()}'
        )
    
    def test_multi_user_gallery_interaction(self):
        """
        複数ユーザーのギャラリー相互作用テスト
        """
        # Step 1: ユーザー1としてログイン
        self.client.login(username='user1', password='testpass123')
        
        # 自分のギャラリーで自分の写真のみが表示されることを確認
        user1_gallery_response = self.client.get(reverse('photos:list'))
        self.assertEqual(user1_gallery_response.status_code, 200)
        self.assertContains(user1_gallery_response, 'ユーザー1の公開写真')
        self.assertContains(user1_gallery_response, 'ユーザー1の非公開写真')
        self.assertNotContains(user1_gallery_response, 'ユーザー2の公開写真')
        self.assertNotContains(user1_gallery_response, 'ユーザー3の公開写真')
        
        # Step 2: 公開ギャラリーで全ユーザーの公開写真が表示されることを確認
        public_gallery_response = self.client.get(reverse('photos:public_gallery'))
        self.assertEqual(public_gallery_response.status_code, 200)
        
        for i in range(3):
            self.assertContains(public_gallery_response, f'ユーザー{i+1}の公開写真')
            self.assertNotContains(public_gallery_response, f'ユーザー{i+1}の非公開写真')
        
        # Step 3: ユーザー2としてログイン
        self.client.login(username='user2', password='testpass123')
        
        # 自分のギャラリーで自分の写真のみが表示されることを確認
        user2_gallery_response = self.client.get(reverse('photos:list'))
        self.assertEqual(user2_gallery_response.status_code, 200)
        self.assertContains(user2_gallery_response, 'ユーザー2の公開写真')
        self.assertContains(user2_gallery_response, 'ユーザー2の非公開写真')
        self.assertNotContains(user2_gallery_response, 'ユーザー1の公開写真')
        self.assertNotContains(user2_gallery_response, 'ユーザー3の公開写真')
        
        # Step 4: 他のユーザーの公開写真詳細にアクセス
        user1_public_photo = Photo.objects.filter(
            owner=self.users[0], 
            is_public=True
        ).first()
        
        detail_response = self.client.get(
            reverse('photos:detail', kwargs={'pk': user1_public_photo.pk})
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'ユーザー1の公開写真')
        
        # 編集・削除ボタンが表示されないことを確認
        self.assertNotContains(detail_response, '編集')
        self.assertNotContains(detail_response, '削除')
    
    def test_user_switching_and_permissions(self):
        """
        ユーザー切り替えと権限テスト
        """
        # ユーザー1でログイン
        self.client.login(username='user1', password='testpass123')
        
        # ユーザー2の写真を編集しようと試行
        user2_photo = Photo.objects.filter(owner=self.users[1]).first()
        
        edit_response = self.client.get(
            reverse('photos:edit', kwargs={'pk': user2_photo.pk})
        )
        
        # 権限エラーでリダイレクトされることを確認
        self.assertEqual(edit_response.status_code, 302)
        
        # ログアウト
        self.client.post(reverse('accounts:logout'))
        
        # ユーザー2でログイン
        self.client.login(username='user2', password='testpass123')
        
        # 今度は自分の写真を編集できることを確認
        edit_response = self.client.get(
            reverse('photos:edit', kwargs={'pk': user2_photo.pk})
        )
        self.assertEqual(edit_response.status_code, 200)
    
    def test_concurrent_user_operations(self):
        """
        同時ユーザー操作のテスト
        """
        # 複数のクライアントを作成
        client1 = Client()
        client2 = Client()
        
        # 異なるユーザーでログイン
        client1.login(username='user1', password='testpass123')
        client2.login(username='user2', password='testpass123')
        
        # 同時に写真をアップロード
        test_image1 = self.create_test_image('concurrent1.jpg')
        test_image2 = self.create_test_image('concurrent2.jpg')
        
        upload_data1 = {
            'title': '同時アップロード1',
            'description': 'ユーザー1の同時アップロード',
            'image': test_image1,
            'is_public': True
        }
        
        upload_data2 = {
            'title': '同時アップロード2',
            'description': 'ユーザー2の同時アップロード',
            'image': test_image2,
            'is_public': True
        }
        
        # 同時アップロード実行
        response1 = client1.post(reverse('photos:upload'), data=upload_data1)
        response2 = client2.post(reverse('photos:upload'), data=upload_data2)
        
        # 両方のアップロードが成功することを確認
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(response2.status_code, 302)
        
        # 写真が正しく作成されたことを確認
        self.assertTrue(
            Photo.objects.filter(
                title='同時アップロード1', 
                owner=self.users[0]
            ).exists()
        )
        self.assertTrue(
            Photo.objects.filter(
                title='同時アップロード2', 
                owner=self.users[1]
            ).exists()
        )
        
        # 公開ギャラリーで両方の写真が表示されることを確認
        public_gallery_response = client1.get(reverse('photos:public_gallery'))
        self.assertEqual(public_gallery_response.status_code, 200)
        self.assertContains(public_gallery_response, '同時アップロード1')
        self.assertContains(public_gallery_response, '同時アップロード2')
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # アップロードされたファイルを削除
        for photo in Photo.objects.all():
            if photo.image and os.path.exists(photo.image.path):
                os.remove(photo.image.path)
            if photo.thumbnail and os.path.exists(photo.thumbnail.path):
                os.remove(photo.thumbnail.path)