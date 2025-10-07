"""
セキュリティ関連のミドルウェア
"""
import time
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    セキュリティヘッダーを追加するミドルウェア
    """
    
    def process_response(self, request, response):
        # Content Security Policy
        if not settings.DEBUG:
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
            response['Content-Security-Policy'] = csp_policy
        
        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Feature Policy (Permissions Policy)
        response['Permissions-Policy'] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )
        
        return response


class LoginAttemptMiddleware(MiddlewareMixin):
    """
    ログイン試行回数を制限するミドルウェア
    """
    
    def process_request(self, request):
        if request.path == '/accounts/login/' and request.method == 'POST':
            ip_address = self.get_client_ip(request)
            cache_key = f'login_attempts_{ip_address}'
            
            # 現在の試行回数を取得
            attempts = cache.get(cache_key, 0)
            
            # 制限を超えている場合
            max_attempts = getattr(settings, 'LOGIN_ATTEMPTS_LIMIT', 5)
            if attempts >= max_attempts:
                timeout = getattr(settings, 'LOGIN_ATTEMPTS_TIMEOUT', 300)  # 5分
                messages.error(
                    request, 
                    f'ログイン試行回数が上限に達しました。{timeout // 60}分後に再試行してください。'
                )
                return HttpResponseForbidden('Too many login attempts')
        
        return None
    
    def process_response(self, request, response):
        if request.path == '/accounts/login/' and request.method == 'POST':
            ip_address = self.get_client_ip(request)
            cache_key = f'login_attempts_{ip_address}'
            timeout = getattr(settings, 'LOGIN_ATTEMPTS_TIMEOUT', 300)
            
            # ログイン失敗の場合（リダイレクトでない場合）
            if response.status_code != 302:
                attempts = cache.get(cache_key, 0) + 1
                cache.set(cache_key, attempts, timeout)
            else:
                # ログイン成功の場合、カウンターをリセット
                cache.delete(cache_key)
        
        return response
    
    def get_client_ip(self, request):
        """クライアントのIPアドレスを取得"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    セッションセキュリティを強化するミドルウェア
    """
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # セッションハイジャック対策：IPアドレスの変更をチェック
            session_ip = request.session.get('session_ip')
            current_ip = self.get_client_ip(request)
            
            if session_ip and session_ip != current_ip:
                # IPアドレスが変更された場合、セッションを無効化
                logout(request)
                messages.warning(
                    request, 
                    'セキュリティ上の理由により、ログアウトされました。再度ログインしてください。'
                )
                return redirect('accounts:login')
            
            # 初回アクセス時にIPアドレスを記録
            if not session_ip:
                request.session['session_ip'] = current_ip
            
            # セッションの最終アクティビティ時間を更新
            request.session['last_activity'] = time.time()
        
        return None
    
    def get_client_ip(self, request):
        """クライアントのIPアドレスを取得"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class FileUploadSecurityMiddleware(MiddlewareMixin):
    """
    ファイルアップロードのセキュリティを強化するミドルウェア
    """
    
    def process_request(self, request):
        if request.method == 'POST' and request.FILES:
            # アップロード頻度制限
            if request.user.is_authenticated:
                user_id = request.user.id
                cache_key = f'upload_rate_{user_id}'
                
                # 1分間のアップロード回数をチェック
                uploads = cache.get(cache_key, 0)
                max_uploads_per_minute = 10
                
                if uploads >= max_uploads_per_minute:
                    messages.error(
                        request, 
                        'アップロード頻度が高すぎます。しばらく待ってから再試行してください。'
                    )
                    return HttpResponseForbidden('Upload rate limit exceeded')
                
                # カウンターを増加
                cache.set(cache_key, uploads + 1, 60)  # 1分間
        
        return None


class XSSProtectionMiddleware(MiddlewareMixin):
    """
    XSS攻撃を防ぐミドルウェア
    """
    
    def process_request(self, request):
        # GET/POSTパラメータのXSSチェック
        for param_dict in [request.GET, request.POST]:
            for key, value in param_dict.items():
                if self.contains_xss(value):
                    messages.error(request, '不正な入力が検出されました。')
                    return HttpResponseForbidden('XSS attempt detected')
        
        return None
    
    def contains_xss(self, value):
        """XSSパターンをチェック"""
        if not isinstance(value, str):
            return False
        
        xss_patterns = [
            '<script',
            'javascript:',
            'onload=',
            'onerror=',
            'onclick=',
            'onmouseover=',
            'eval(',
            'expression(',
        ]
        
        value_lower = value.lower()
        return any(pattern in value_lower for pattern in xss_patterns)