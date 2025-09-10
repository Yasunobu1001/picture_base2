from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.urls import reverse
from django.contrib.messages import get_messages
from PIL import Image
import tempfile
import os
from .forms import CustomUserCreationForm, CustomAuthenticationForm

User = get_user_model()


class CustomUserModelTest(TestCase):
    """CustomUserモデルのテストケース"""

    def setUp(self):
        """テスト用のデータを準備"""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }

    def test_create_user(self):
        """ユーザーの作成テスト"""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertIsNotNone(user.created_at)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """スーパーユーザーの作成テスト"""
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.assertEqual(admin_user.username, 'admin')
        self.assertEqual(admin_user.email, 'admin@example.com')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_email_unique_constraint(self):
        """メールアドレスの一意制約テスト"""
        User.objects.create_user(**self.user_data)
        
        # 同じメールアドレスで別のユーザーを作成しようとするとエラーになる
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='testuser2',
                email='test@example.com',  # 同じメールアドレス
                password='testpass456'
            )

    def test_user_str_representation(self):
        """ユーザーの文字列表現テスト"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'testuser')

    def test_profile_picture_field(self):
        """プロフィール画像フィールドのテスト"""
        # テスト用の画像ファイルを作成
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            # 小さなテスト画像を作成
            image = Image.new('RGB', (100, 100), color='red')
            image.save(tmp_file, format='JPEG')
            tmp_file.flush()
            
            # ファイルを読み込んでSimpleUploadedFileを作成
            with open(tmp_file.name, 'rb') as f:
                uploaded_file = SimpleUploadedFile(
                    name='test_profile.jpg',
                    content=f.read(),
                    content_type='image/jpeg'
                )
            
            # ユーザーを作成してプロフィール画像を設定
            user = User.objects.create_user(**self.user_data)
            user.profile_picture = uploaded_file
            user.save()
            
            # プロフィール画像が正しく保存されているかテスト
            self.assertTrue(user.profile_picture)
            self.assertIn('profiles/', user.profile_picture.name)
            
            # クリーンアップ
            if user.profile_picture:
                user.profile_picture.delete()
            os.unlink(tmp_file.name)

    def test_profile_picture_optional(self):
        """プロフィール画像が任意であることのテスト"""
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.profile_picture)  # プロフィール画像なしでも作成可能

    def test_user_verbose_names(self):
        """モデルのverbose_nameテスト"""
        self.assertEqual(User._meta.verbose_name, 'ユーザー')
        self.assertEqual(User._meta.verbose_name_plural, 'ユーザー')

    def test_email_field_verbose_name(self):
        """emailフィールドのverbose_nameテスト"""
        email_field = User._meta.get_field('email')
        self.assertEqual(email_field.verbose_name, 'メールアドレス')

    def test_profile_picture_field_verbose_name(self):
        """profile_pictureフィールドのverbose_nameテスト"""
        profile_picture_field = User._meta.get_field('profile_picture')
        self.assertEqual(profile_picture_field.verbose_name, 'プロフィール画像')

    def test_created_at_field_verbose_name(self):
        """created_atフィールドのverbose_nameテスト"""
        created_at_field = User._meta.get_field('created_at')
        self.assertEqual(created_at_field.verbose_name, '作成日時')


class CustomUserCreationFormTest(TestCase):
    """CustomUserCreationFormのテストケース"""

    def test_valid_form(self):
        """有効なフォームデータのテスト"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_email_required(self):
        """メールアドレス必須のテスト"""
        form_data = {
            'username': 'testuser',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_duplicate_email(self):
        """重複メールアドレスのテスト"""
        # 既存ユーザーを作成
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='testpass123'
        )
        
        # 同じメールアドレスで新規登録を試行
        form_data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_password_mismatch(self):
        """パスワード不一致のテスト"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'differentpass'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_form_save(self):
        """フォーム保存のテスト"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))


class CustomAuthenticationFormTest(TestCase):
    """CustomAuthenticationFormのテストケース"""

    def setUp(self):
        """テスト用ユーザーを作成"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_with_username(self):
        """ユーザー名でのログインテスト"""
        form_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        form = CustomAuthenticationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_login_with_email(self):
        """メールアドレスでのログインテスト"""
        form_data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }
        form = CustomAuthenticationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_credentials(self):
        """無効な認証情報のテスト"""
        form_data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        form = CustomAuthenticationForm(data=form_data)
        self.assertFalse(form.is_valid())


class AuthenticationViewsTest(TestCase):
    """認証ビューのテストケース"""

    def setUp(self):
        """テスト用のクライアントとユーザーを準備"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_signup_view_get(self):
        """サインアップページのGETリクエストテスト"""
        response = self.client.get(reverse('accounts:signup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ユーザー名')
        self.assertContains(response, 'メールアドレス')

    def test_signup_view_post_valid(self):
        """有効なサインアップPOSTリクエストテスト"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        response = self.client.post(reverse('accounts:signup'), data=form_data)
        
        # リダイレクトされることを確認
        self.assertEqual(response.status_code, 302)
        
        # ユーザーが作成されたことを確認
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # 成功メッセージが設定されていることを確認
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('アカウントが作成されました' in str(message) for message in messages))

    def test_signup_view_post_invalid(self):
        """無効なサインアップPOSTリクエストテスト"""
        form_data = {
            'username': 'newuser',
            'email': 'invalid-email',  # 無効なメールアドレス
            'password1': 'newpass123',
            'password2': 'differentpass'  # パスワード不一致
        }
        response = self.client.post(reverse('accounts:signup'), data=form_data)
        
        # フォームエラーでページが再表示される
        self.assertEqual(response.status_code, 200)
        
        # ユーザーが作成されていないことを確認
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_login_view_get(self):
        """ログインページのGETリクエストテスト"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ユーザー名またはメールアドレス')
        self.assertContains(response, 'パスワード')

    def test_login_view_post_valid(self):
        """有効なログインPOSTリクエストテスト"""
        form_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(reverse('accounts:login'), data=form_data)
        
        # リダイレクトされることを確認
        self.assertEqual(response.status_code, 302)
        
        # ユーザーがログインしていることを確認
        user = response.wsgi_request.user
        self.assertTrue(user.is_authenticated)

    def test_login_view_post_invalid(self):
        """無効なログインPOSTリクエストテスト"""
        form_data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(reverse('accounts:login'), data=form_data)
        
        # フォームエラーでページが再表示される
        self.assertEqual(response.status_code, 200)
        
        # エラーメッセージが設定されていることを確認
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('正しくありません' in str(message) for message in messages))

    def test_login_with_email(self):
        """メールアドレスでのログインテスト"""
        form_data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(reverse('accounts:login'), data=form_data)
        
        # リダイレクトされることを確認
        self.assertEqual(response.status_code, 302)

    def test_logout_view(self):
        """ログアウトビューのテスト"""
        # まずログイン
        self.client.login(username='testuser', password='testpass123')
        
        # ログアウト
        response = self.client.post(reverse('accounts:logout'))
        
        # リダイレクトされることを確認
        self.assertEqual(response.status_code, 302)
        
        # ログアウトメッセージが設定されていることを確認
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('ログアウトしました' in str(message) for message in messages))

    def test_authenticated_user_redirect(self):
        """認証済みユーザーのリダイレクトテスト"""
        # ログイン
        self.client.login(username='testuser', password='testpass123')
        
        # ログインページにアクセス
        response = self.client.get(reverse('accounts:login'))
        
        # リダイレクトされることを確認
        self.assertEqual(response.status_code, 302)