from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """カスタムユーザー登録フォーム"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'メールアドレス'
        }),
        label='メールアドレス'
    )
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'ユーザー名'
        }),
        label='ユーザー名'
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'パスワード'
        }),
        label='パスワード'
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'パスワード（確認）'
        }),
        label='パスワード（確認）'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        """メールアドレスの重複チェック"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('このメールアドレスは既に使用されています。')
        return email

    def save(self, commit=True):
        """ユーザーを保存"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """カスタムログインフォーム"""
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'ユーザー名またはメールアドレス'
        }),
        label='ユーザー名またはメールアドレス'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'パスワード'
        }),
        label='パスワード'
    )

    def clean_username(self):
        """ユーザー名またはメールアドレスでの認証を可能にする"""
        username = self.cleaned_data.get('username')
        
        # メールアドレスが入力された場合、対応するユーザー名を取得
        if '@' in username:
            try:
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                pass
        
        return username