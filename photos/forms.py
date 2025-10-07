"""
写真アプリ用のフォーム（セキュリティ強化版）
"""
import re
import html
from django import forms
from django.core.exceptions import ValidationError
from .models import Photo
from .utils import sanitize_filename


class PhotoUploadForm(forms.ModelForm):
    """写真アップロード用フォーム"""
    
    class Meta:
        model = Photo
        fields = ['title', 'description', 'image', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '写真のタイトルを入力してください',
                'maxlength': '100'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': '写真の説明を入力してください（任意）',
                'rows': 4
            }),
            'image': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/jpeg,image/jpg,image/png,image/gif',
                'id': 'photo-upload-input',
                'capture': 'environment'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            })
        }
        labels = {
            'title': 'タイトル',
            'description': '説明',
            'image': '写真ファイル',
            'is_public': '公開設定'
        }
        help_texts = {
            'title': '写真のタイトルを入力してください（100文字以内）',
            'description': '写真の説明や撮影場所などを入力してください（任意）',
            'image': 'JPEG、PNG、GIFファイル（10MB以下）をアップロードしてください',
            'is_public': 'チェックすると他のユーザーも閲覧できます'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 必須フィールドにアスタリスクを追加
        self.fields['title'].required = True
        self.fields['image'].required = True
        
    def clean_title(self):
        """タイトルのセキュアなバリデーション"""
        title = self.cleaned_data.get('title')
        if title:
            title = title.strip()
            if len(title) == 0:
                raise forms.ValidationError('タイトルを入力してください。')
            if len(title) > 100:
                raise forms.ValidationError('タイトルは100文字以内で入力してください。')
            
            # XSS対策：HTMLタグをエスケープ
            title = html.escape(title)
            
            # 危険なパターンをチェック
            if self._contains_dangerous_content(title):
                raise forms.ValidationError('タイトルに不正な内容が含まれています。')
        
        return title
    
    def clean_description(self):
        """説明のセキュアなバリデーション"""
        description = self.cleaned_data.get('description')
        if description:
            description = description.strip()
            
            # 長さ制限
            if len(description) > 1000:
                raise forms.ValidationError('説明は1000文字以内で入力してください。')
            
            # XSS対策：HTMLタグをエスケープ
            description = html.escape(description)
            
            # 危険なパターンをチェック
            if self._contains_dangerous_content(description):
                raise forms.ValidationError('説明に不正な内容が含まれています。')
        
        return description
    
    def clean_image(self):
        """画像ファイルのセキュアなバリデーション"""
        image = self.cleaned_data.get('image')
        if image:
            # ファイルサイズチェック（10MB）
            max_size = 10 * 1024 * 1024
            if image.size > max_size:
                raise forms.ValidationError('ファイルサイズが大きすぎます。10MB以下のファイルをアップロードしてください。')
            
            # ファイル形式チェック
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if image.content_type not in allowed_types:
                raise forms.ValidationError('サポートされていないファイル形式です。JPEG、PNG、GIFファイルのみアップロード可能です。')
            
            # ファイル名のサニタイズ
            if hasattr(image, 'name') and image.name:
                image.name = sanitize_filename(image.name)
        
        return image
    
    def _contains_dangerous_content(self, text):
        """危険なコンテンツをチェック"""
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'vbscript:',
            r'data:text/html',
        ]
        
        text_lower = text.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                return True
        
        return False


class PhotoEditForm(forms.ModelForm):
    """写真編集用フォーム"""
    
    class Meta:
        model = Photo
        fields = ['title', 'description', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '写真のタイトルを入力してください',
                'maxlength': '100'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '写真の説明を入力してください（任意）',
                'rows': 4
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            })
        }
        labels = {
            'title': 'タイトル',
            'description': '説明',
            'is_public': '公開設定'
        }
        help_texts = {
            'title': '写真のタイトルを入力してください（100文字以内）',
            'description': '写真の説明や撮影場所などを入力してください（任意）',
            'is_public': 'チェックすると他のユーザーも閲覧できます'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 必須フィールドにアスタリスクを追加
        self.fields['title'].required = True
        
    def clean_title(self):
        """タイトルのセキュアなバリデーション"""
        title = self.cleaned_data.get('title')
        if title:
            title = title.strip()
            if len(title) == 0:
                raise forms.ValidationError('タイトルを入力してください。')
            if len(title) > 100:
                raise forms.ValidationError('タイトルは100文字以内で入力してください。')
            
            # XSS対策：HTMLタグをエスケープ
            title = html.escape(title)
            
            # 危険なパターンをチェック
            if self._contains_dangerous_content(title):
                raise forms.ValidationError('タイトルに不正な内容が含まれています。')
        
        return title
    
    def clean_description(self):
        """説明のセキュアなバリデーション"""
        description = self.cleaned_data.get('description')
        if description:
            description = description.strip()
            
            # 長さ制限
            if len(description) > 1000:
                raise forms.ValidationError('説明は1000文字以内で入力してください。')
            
            # XSS対策：HTMLタグをエスケープ
            description = html.escape(description)
            
            # 危険なパターンをチェック
            if self._contains_dangerous_content(description):
                raise forms.ValidationError('説明に不正な内容が含まれています。')
        
        return description
    
    def _contains_dangerous_content(self, text):
        """危険なコンテンツをチェック"""
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'vbscript:',
            r'data:text/html',
        ]
        
        text_lower = text.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                return True
        
        return False