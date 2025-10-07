"""
写真アプリのビュー（最適化済み）
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.core.cache import cache
from django.http import Http404
from django.db.models import Count, Q
import os
from .models import Photo
from .forms import PhotoUploadForm, PhotoEditForm
from .db_optimization import QueryOptimizer, CacheOptimizer, monitor_query_performance


class PhotoUploadView(LoginRequiredMixin, CreateView):
    """写真アップロードビュー"""
    model = Photo
    form_class = PhotoUploadForm
    template_name = 'photos/photo_upload.html'
    success_url = reverse_lazy('photos:list')
    
    def form_valid(self, form):
        """フォームが有効な場合の処理"""
        # 現在のユーザーを所有者として設定
        form.instance.owner = self.request.user
        
        try:
            # 写真を保存
            response = super().form_valid(form)
            
            # 成功メッセージを表示
            messages.success(
                self.request, 
                f'写真「{form.instance.title}」をアップロードしました。'
            )
            
            return response
            
        except Exception as e:
            # エラーが発生した場合
            messages.error(
                self.request,
                '写真のアップロードに失敗しました。もう一度お試しください。'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """フォームが無効な場合の処理"""
        # エラーメッセージを表示
        messages.error(
            self.request,
            'アップロードに失敗しました。入力内容を確認してください。'
        )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """テンプレートに渡すコンテキストデータ"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = '写真をアップロード'
        return context


class PhotoListView(LoginRequiredMixin, ListView):
    """写真一覧ビュー（ユーザーの写真のみ表示）"""
    model = Photo
    template_name = 'photos/photo_list.html'
    context_object_name = 'photos'
    paginate_by = 12  # 1ページあたり12枚の写真を表示
    
    def get_queryset(self):
        """現在のユーザーの写真のみを取得（作成日時降順、最適化済み）"""
        return Photo.objects.filter(
            owner=self.request.user
        ).select_related('owner').only(
            'id', 'title', 'description', 'image', 'thumbnail', 
            'is_public', 'created_at', 'owner__username'
        ).order_by('-created_at')
    
    @monitor_query_performance
    def get_context_data(self, **kwargs):
        """テンプレートに渡すコンテキストデータ（最適化済み）"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'マイギャラリー'
        
        # ユーザーの写真数をキャッシュから取得
        cache_key = f'user_photo_count_{self.request.user.id}'
        total_photos = CacheOptimizer.get_cached_photo_count(
            cache_key,
            lambda: QueryOptimizer.get_user_photo_count(self.request.user)
        )
        context['total_photos'] = total_photos
        
        return context


class PhotoDetailView(LoginRequiredMixin, DetailView):
    """写真詳細ビュー"""
    model = Photo
    template_name = 'photos/photo_detail.html'
    context_object_name = 'photo'
    
    def get_object(self, queryset=None):
        """写真オブジェクトを取得（権限チェック付き、最適化済み）"""
        photo = get_object_or_404(
            Photo.objects.select_related('owner'), 
            pk=self.kwargs['pk']
        )
        
        # 写真の所有者または公開写真の場合のみアクセス可能
        if photo.owner != self.request.user and not photo.is_public:
            # 非公開写真で所有者でない場合は404を返す
            raise Http404("写真が見つかりません。")
        
        return photo
    
    def get_context_data(self, **kwargs):
        """テンプレートに渡すコンテキストデータ"""
        context = super().get_context_data(**kwargs)
        photo = self.get_object()
        
        # 所有者かどうかをチェック
        context['is_owner'] = photo.owner == self.request.user
        context['page_title'] = photo.title or '写真詳細'
        
        # 前後の写真を取得（最適化済み）
        if context['is_owner']:
            # 所有者の場合は自分の写真から前後を取得
            base_queryset = Photo.objects.filter(owner=self.request.user)
        else:
            # 他のユーザーの写真の場合は公開写真から前後を取得
            base_queryset = Photo.objects.filter(
                owner=photo.owner, 
                is_public=True
            )
        
        # 前の写真（現在の写真より新しい写真の中で最も古いもの）
        prev_photo = base_queryset.filter(
            created_at__gt=photo.created_at
        ).order_by('created_at').only('id', 'title').first()
        
        # 次の写真（現在の写真より古い写真の中で最も新しいもの）
        next_photo = base_queryset.filter(
            created_at__lt=photo.created_at
        ).order_by('-created_at').only('id', 'title').first()
        
        context['prev_photo'] = prev_photo
        context['next_photo'] = next_photo
        
        return context


class PhotoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """写真編集ビュー"""
    model = Photo
    form_class = PhotoEditForm
    template_name = 'photos/photo_edit.html'
    context_object_name = 'photo'
    
    def test_func(self):
        """所有者権限チェック"""
        photo = self.get_object()
        return photo.owner == self.request.user
    
    def handle_no_permission(self):
        """権限がない場合の処理"""
        messages.error(self.request, 'この写真を編集する権限がありません。')
        return redirect('photos:list')
    
    def get_success_url(self):
        """編集成功後のリダイレクト先"""
        return reverse_lazy('photos:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        """フォームが有効な場合の処理"""
        try:
            response = super().form_valid(form)
            messages.success(
                self.request, 
                f'写真「{form.instance.title}」を更新しました。'
            )
            return response
        except Exception as e:
            messages.error(
                self.request,
                '写真の更新に失敗しました。もう一度お試しください。'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """フォームが無効な場合の処理"""
        messages.error(
            self.request,
            '更新に失敗しました。入力内容を確認してください。'
        )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """テンプレートに渡すコンテキストデータ"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'写真を編集 - {self.object.title}'
        return context


class PhotoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """写真削除ビュー"""
    model = Photo
    template_name = 'photos/photo_confirm_delete.html'
    context_object_name = 'photo'
    success_url = reverse_lazy('photos:list')
    
    def test_func(self):
        """所有者権限チェック"""
        photo = self.get_object()
        return photo.owner == self.request.user
    
    def handle_no_permission(self):
        """権限がない場合の処理"""
        messages.error(self.request, 'この写真を削除する権限がありません。')
        return redirect('photos:list')
    
    def delete(self, request, *args, **kwargs):
        """削除処理（ファイルシステムからも削除）"""
        photo = self.get_object()
        photo_title = photo.title
        
        try:
            # データベースから削除（signalsでストレージ削除を処理）
            response = super().delete(request, *args, **kwargs)
            
            messages.success(
                request, 
                f'写真「{photo_title}」を削除しました。'
            )
            return response
            
        except Exception as e:
            messages.error(
                request,
                '写真の削除に失敗しました。もう一度お試しください。'
            )
            return redirect('photos:detail', pk=photo.pk)
    
    def get_context_data(self, **kwargs):
        """テンプレートに渡すコンテキストデータ"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'写真を削除 - {self.object.title}'
        return context


class PublicGalleryView(ListView):
    """公開ギャラリービュー（全ユーザーの公開写真を表示）"""
    model = Photo
    template_name = 'photos/public_gallery.html'
    context_object_name = 'photos'
    paginate_by = 12  # 1ページあたり12枚の写真を表示
    
    def get_queryset(self):
        """公開写真のみを取得（作成日時降順、最適化済み）"""
        return Photo.objects.filter(
            is_public=True
        ).select_related('owner').only(
            'id', 'title', 'description', 'image', 'thumbnail', 
            'created_at', 'owner__username', 'owner__profile_picture'
        ).order_by('-created_at')
    
    @monitor_query_performance
    def get_context_data(self, **kwargs):
        """テンプレートに渡すコンテキストデータ（最適化済み）"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = '公開ギャラリー'
        
        # 公開写真数をキャッシュから取得
        total_photos = CacheOptimizer.get_cached_photo_count(
            'public_photo_count',
            QueryOptimizer.get_public_photo_count
        )
        context['total_photos'] = total_photos
        
        return context
