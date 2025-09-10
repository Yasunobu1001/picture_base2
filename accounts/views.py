from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomUserCreationForm, CustomAuthenticationForm


class SignUpView(CreateView):
    """ユーザー登録ビュー"""
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        """フォームが有効な場合の処理"""
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        messages.success(self.request, f'{username}さん、アカウントが作成されました！ログインしてください。')
        return response

    def form_invalid(self, form):
        """フォームが無効な場合の処理"""
        messages.error(self.request, 'アカウント作成に失敗しました。入力内容を確認してください。')
        return super().form_invalid(form)


class CustomLoginView(LoginView):
    """カスタムログインビュー"""
    form_class = CustomAuthenticationForm
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        """ログイン成功時の処理"""
        username = form.get_user().username
        messages.success(self.request, f'{username}さん、おかえりなさい！')
        return super().form_valid(form)

    def form_invalid(self, form):
        """ログイン失敗時の処理"""
        messages.error(self.request, 'ユーザー名またはパスワードが正しくありません。')
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """カスタムログアウトビュー"""
    
    def dispatch(self, request, *args, **kwargs):
        """ログアウト時の処理"""
        if request.user.is_authenticated:
            messages.success(request, 'ログアウトしました。')
        return super().dispatch(request, *args, **kwargs)