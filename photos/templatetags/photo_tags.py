"""
写真表示用のカスタムテンプレートタグ
"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def responsive_image(photo, css_class="", alt_text="", loading="lazy"):
    """
    レスポンシブ画像タグを生成
    
    Args:
        photo: Photoオブジェクト
        css_class: CSSクラス
        alt_text: alt属性のテキスト
        loading: loading属性の値
    
    Returns:
        HTMLの画像タグ
    """
    if not photo or not photo.image:
        return ""
    
    # alt属性の設定
    if not alt_text:
        alt_text = photo.title or f"写真 {photo.id}"
    
    # サムネイルがある場合は使用、ない場合は元画像
    image_url = photo.thumbnail.url if photo.thumbnail else photo.image.url
    
    # 基本的な画像タグ
    img_tag = f'''<img src="{image_url}" 
                      alt="{alt_text}" 
                      class="{css_class}"
                      loading="{loading}"
                      decoding="async">'''
    
    return mark_safe(img_tag)


@register.simple_tag
def lazy_image(photo, css_class="", alt_text="", placeholder_class="bg-gray-200"):
    """
    遅延読み込み対応の画像タグを生成（Intersection Observer使用）
    
    Args:
        photo: Photoオブジェクト
        css_class: CSSクラス
        alt_text: alt属性のテキスト
        placeholder_class: プレースホルダーのCSSクラス
    
    Returns:
        HTMLの画像タグ
    """
    if not photo or not photo.image:
        return ""
    
    # alt属性の設定
    if not alt_text:
        alt_text = photo.title or f"写真 {photo.id}"
    
    # サムネイルがある場合は使用、ない場合は元画像
    image_url = photo.thumbnail.url if photo.thumbnail else photo.image.url
    
    # 遅延読み込み対応の画像タグ
    img_tag = f'''<img data-src="{image_url}" 
                      alt="{alt_text}" 
                      class="lazy-image {css_class} {placeholder_class}"
                      loading="lazy"
                      decoding="async">'''
    
    return mark_safe(img_tag)


@register.inclusion_tag('photos/partials/photo_card.html')
def photo_card(photo, show_author=False, card_class=""):
    """
    写真カードコンポーネント
    
    Args:
        photo: Photoオブジェクト
        show_author: 作者情報を表示するか
        card_class: カードのCSSクラス
    
    Returns:
        テンプレートコンテキスト
    """
    return {
        'photo': photo,
        'show_author': show_author,
        'card_class': card_class,
    }


@register.filter
def file_size_mb(file_field):
    """
    ファイルサイズをMB単位で表示
    
    Args:
        file_field: FileFieldオブジェクト
    
    Returns:
        MB単位のファイルサイズ文字列
    """
    if not file_field:
        return "0 MB"
    
    try:
        size_mb = file_field.size / (1024 * 1024)
        return f"{size_mb:.1f} MB"
    except (AttributeError, OSError):
        return "不明"


@register.filter
def image_dimensions(image_field):
    """
    画像の寸法を取得
    
    Args:
        image_field: ImageFieldオブジェクト
    
    Returns:
        寸法文字列（例: "1920x1080"）
    """
    if not image_field:
        return "不明"
    
    try:
        return f"{image_field.width}x{image_field.height}"
    except (AttributeError, OSError):
        return "不明"