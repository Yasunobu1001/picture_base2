"""
写真アプリ用のユーティリティ関数
"""
import os
from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO


def validate_image_file(file):
    """
    画像ファイルのセキュアなバリデーション
    - ファイル形式: JPEG, PNG, GIF
    - ファイルサイズ: 10MB以下
    - セキュリティチェック: 悪意のあるファイルの検出
    """
    # ファイルサイズチェック (10MB = 10 * 1024 * 1024 bytes)
    max_size = 10 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError(f'ファイルサイズが大きすぎます。{max_size // (1024 * 1024)}MB以下にしてください。')
    
    # 最小ファイルサイズチェック（空ファイルや極小ファイルを拒否）
    min_size = 100  # 100 bytes
    if file.size < min_size:
        raise ValidationError('ファイルサイズが小さすぎます。有効な画像ファイルをアップロードしてください。')
    
    # ファイル形式チェック（Pillowが解釈できる形式を優先）
    allowed_formats = ['JPEG', 'PNG', 'GIF', 'WEBP', 'HEIC', 'HEIF']
    # 拡張子は許容範囲を広げる（危険拡張子のみ拒否）
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.heif']
    dangerous_extensions = ['.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar', '.php', '.asp', '.jsp']
    
    # 拡張子チェック（危険拡張子は拒否、それ以外は後段の実体チェックで判定）
    file_extension = os.path.splitext(file.name)[1].lower()
    if file_extension in dangerous_extensions:
        raise ValidationError('セキュリティ上の理由により、このファイル形式はアップロードできません。')
    
    # ここでの拡張子は参考情報として扱う（危険拡張子は既にブロック済み）
    
    # ファイル名のセキュリティチェック
    if not _is_safe_filename(file.name):
        raise ValidationError('ファイル名に無効な文字が含まれています。')
    
    # 実際の画像ファイルかチェック
    try:
        # ファイルポインタを先頭に戻す
        file.seek(0)
        image = Image.open(file)
        
        # 画像形式チェック（実体優先）
        if image.format not in allowed_formats:
            raise ValidationError('サポートされていない画像形式です。JPEG、PNG、GIF、WEBP、HEIC形式のみアップロード可能です。')
        
        # 画像サイズの妥当性チェック
        width, height = image.size
        max_dimension = 10000  # 最大10000px
        if width > max_dimension or height > max_dimension:
            raise ValidationError(f'画像サイズが大きすぎます。{max_dimension}x{max_dimension}px以下にしてください。')
        
        # 最小画像サイズチェック
        min_dimension = 10  # 最小10px
        if width < min_dimension or height < min_dimension:
            raise ValidationError(f'画像サイズが小さすぎます。{min_dimension}x{min_dimension}px以上にしてください。')
        
        # 画像が破損していないかチェック
        image.verify()
        
        # ファイルポインタを先頭に戻す（後続処理のため）
        file.seek(0)
        
        # EXIFデータのセキュリティチェック
        _check_exif_security(file)
        
    except ValidationError:
        # ValidationErrorはそのまま再発生
        raise
    except Exception as e:
        raise ValidationError('有効な画像ファイルではありません。')
    
    return file


def _is_safe_filename(filename):
    """
    ファイル名の安全性をチェック
    
    Args:
        filename: チェックするファイル名
    
    Returns:
        bool: 安全な場合True
    """
    import re
    
    # 危険な文字パターン
    dangerous_patterns = [
        r'\.\./',  # ディレクトリトラバーサル
        r'\\',     # バックスラッシュ
        r'[<>:"|?*]',  # Windows予約文字
        r'^\.',    # 隠しファイル
        r'^\s',    # 先頭空白
        r'\s$',    # 末尾空白
    ]
    
    # 予約されたファイル名（Windows）
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    # ファイル名の長さチェック
    if len(filename) > 255:
        return False
    
    # 危険なパターンのチェック
    for pattern in dangerous_patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            return False
    
    # 予約名のチェック
    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in reserved_names:
        return False
    
    return True


def _check_exif_security(file):
    """
    EXIFデータのセキュリティチェック
    
    Args:
        file: 画像ファイル
    """
    try:
        file.seek(0)
        image = Image.open(file)
        
        # EXIFデータを取得
        exif_data = image._getexif()
        if exif_data:
            # 危険なEXIFタグをチェック（例：実行可能コードを含む可能性のあるタグ）
            dangerous_tags = [
                'MakerNote',  # メーカー固有データ（実行可能コードを含む可能性）
                'UserComment',  # ユーザーコメント（スクリプトを含む可能性）
            ]
            
            for tag_id, value in exif_data.items():
                # 文字列値の場合、スクリプトタグをチェック
                if isinstance(value, str):
                    if '<script' in value.lower() or 'javascript:' in value.lower():
                        raise ValidationError('画像に不正なデータが含まれています。')
        
        file.seek(0)
        
    except ValidationError:
        raise
    except Exception:
        # EXIFチェックに失敗してもエラーにしない
        pass


def sanitize_filename(filename):
    """
    ファイル名をサニタイズ
    
    Args:
        filename: 元のファイル名
    
    Returns:
        str: サニタイズされたファイル名
    """
    import re
    import unicodedata
    
    # Unicode正規化
    filename = unicodedata.normalize('NFKC', filename)
    
    # 危険な文字を除去
    filename = re.sub(r'[<>:"|?*\\]', '', filename)
    
    # ディレクトリトラバーサル対策
    filename = re.sub(r'\.\./', '', filename)
    
    # 先頭・末尾の空白とドットを除去
    filename = filename.strip(' .')
    
    # 長すぎる場合は切り詰め
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:100-len(ext)] + ext
    
    # 空の場合はデフォルト名
    if not filename:
        filename = 'image.jpg'
    
    return filename


def create_thumbnail(image_file, size=(300, 300), quality=85):
    """
    サムネイル画像を生成（最適化済み）
    
    Args:
        image_file: 元画像ファイル
        size: サムネイルサイズ (width, height)
        quality: JPEG品質（1-100）
    
    Returns:
        InMemoryUploadedFile: サムネイル画像ファイル
    """
    try:
        # ファイルポインタを先頭に戻す
        image_file.seek(0)
        
        # 画像を開く
        image = Image.open(image_file)
        
        # EXIF情報に基づいて画像を回転（スマートフォン写真対応）
        try:
            from PIL.ExifTags import ORIENTATION
            exif = image._getexif()
            if exif is not None:
                for tag, value in exif.items():
                    if tag == ORIENTATION:
                        if value == 3:
                            image = image.rotate(180, expand=True)
                        elif value == 6:
                            image = image.rotate(270, expand=True)
                        elif value == 8:
                            image = image.rotate(90, expand=True)
                        break
        except (AttributeError, KeyError, TypeError):
            # EXIF情報がない場合は無視
            pass
        
        # RGBAモードの場合はRGBに変換（JPEG保存のため）
        if image.mode in ('RGBA', 'LA', 'P'):
            # 白背景を作成
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # サムネイル作成（アスペクト比を保持、高品質リサンプリング）
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        # シャープネス調整（サムネイル用）
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.1)  # 軽微なシャープネス向上
        
        # BytesIOオブジェクトに保存
        thumb_io = BytesIO()
        
        # 元のファイル名からサムネイル名を生成
        original_name = os.path.splitext(image_file.name)[0]
        thumb_name = f"{original_name}_thumb.jpg"
        
        # JPEG形式で保存（最適化オプション付き）
        image.save(
            thumb_io, 
            format='JPEG', 
            quality=quality, 
            optimize=True,
            progressive=True  # プログレッシブJPEG
        )
        thumb_io.seek(0)
        
        # InMemoryUploadedFileとして返す
        thumbnail = InMemoryUploadedFile(
            thumb_io,
            None,
            thumb_name,
            'image/jpeg',
            thumb_io.getbuffer().nbytes,
            None
        )
        
        # 元ファイルのポインタを先頭に戻す
        image_file.seek(0)
        
        return thumbnail
        
    except Exception as e:
        # サムネイル生成に失敗した場合はNoneを返す
        return None


def get_image_info(image_file):
    """
    画像ファイルの情報を取得
    
    Args:
        image_file: 画像ファイル
    
    Returns:
        dict: 画像情報（幅、高さ、形式、サイズ）
    """
    try:
        image_file.seek(0)
        image = Image.open(image_file)
        
        info = {
            'width': image.width,
            'height': image.height,
            'format': image.format,
            'mode': image.mode,
            'size_bytes': image_file.size,
            'size_mb': round(image_file.size / (1024 * 1024), 2)
        }
        
        image_file.seek(0)
        return info
        
    except Exception as e:
        return None


def resize_image(image_file, max_width=1920, max_height=1080, quality=85):
    """
    画像をリサイズ（最大サイズを指定、最適化済み）
    
    Args:
        image_file: 元画像ファイル
        max_width: 最大幅
        max_height: 最大高さ
        quality: JPEG品質（1-100）
    
    Returns:
        InMemoryUploadedFile: リサイズされた画像ファイル
    """
    try:
        image_file.seek(0)
        image = Image.open(image_file)
        
        # EXIF情報に基づいて画像を回転
        try:
            from PIL.ExifTags import ORIENTATION
            exif = image._getexif()
            if exif is not None:
                for tag, value in exif.items():
                    if tag == ORIENTATION:
                        if value == 3:
                            image = image.rotate(180, expand=True)
                        elif value == 6:
                            image = image.rotate(270, expand=True)
                        elif value == 8:
                            image = image.rotate(90, expand=True)
                        break
        except (AttributeError, KeyError, TypeError):
            pass
        
        # 現在のサイズ
        current_width, current_height = image.size
        
        # リサイズが必要かチェック
        if current_width <= max_width and current_height <= max_height:
            # サイズは適切だが、圧縮は実行
            return compress_image(image_file, quality=quality)
        
        # アスペクト比を保持してリサイズ
        ratio = min(max_width / current_width, max_height / current_height)
        new_width = int(current_width * ratio)
        new_height = int(current_height * ratio)
        
        # リサイズ実行（高品質リサンプリング）
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # RGBAモードの場合はRGBに変換
        if resized_image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', resized_image.size, (255, 255, 255))
            if resized_image.mode == 'P':
                resized_image = resized_image.convert('RGBA')
            background.paste(resized_image, mask=resized_image.split()[-1] if resized_image.mode == 'RGBA' else None)
            resized_image = background
        
        # BytesIOに保存
        output = BytesIO()
        resized_image.save(
            output, 
            format='JPEG', 
            quality=quality, 
            optimize=True,
            progressive=True
        )
        output.seek(0)
        
        # 新しいファイル名
        original_name = os.path.splitext(image_file.name)[0]
        new_name = f"{original_name}.jpg"  # リサイズ後は常にJPEG
        
        # InMemoryUploadedFileとして返す
        resized_file = InMemoryUploadedFile(
            output,
            None,
            new_name,
            'image/jpeg',
            output.getbuffer().nbytes,
            None
        )
        
        return resized_file
        
    except Exception as e:
        # リサイズに失敗した場合は元ファイルを返す
        image_file.seek(0)
        return image_file


def compress_image(image_file, quality=85, max_file_size_mb=5):
    """
    画像を圧縮（ファイルサイズ最適化）
    
    Args:
        image_file: 元画像ファイル
        quality: 初期JPEG品質（1-100）
        max_file_size_mb: 最大ファイルサイズ（MB）
    
    Returns:
        InMemoryUploadedFile: 圧縮された画像ファイル
    """
    try:
        image_file.seek(0)
        image = Image.open(image_file)
        
        # RGBAモードの場合はRGBに変換
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # 段階的に品質を下げてファイルサイズを調整
        max_size_bytes = max_file_size_mb * 1024 * 1024
        current_quality = quality
        
        while current_quality >= 60:  # 最低品質60%まで
            output = BytesIO()
            image.save(
                output, 
                format='JPEG', 
                quality=current_quality, 
                optimize=True,
                progressive=True
            )
            
            if output.getbuffer().nbytes <= max_size_bytes:
                break
                
            current_quality -= 5
            output.close()
        
        output.seek(0)
        
        # 新しいファイル名
        original_name = os.path.splitext(image_file.name)[0]
        new_name = f"{original_name}.jpg"
        
        # InMemoryUploadedFileとして返す
        compressed_file = InMemoryUploadedFile(
            output,
            None,
            new_name,
            'image/jpeg',
            output.getbuffer().nbytes,
            None
        )
        
        return compressed_file
        
    except Exception as e:
        # 圧縮に失敗した場合は元ファイルを返す
        image_file.seek(0)
        return image_file


def create_multiple_sizes(image_file):
    """
    複数サイズの画像を生成（レスポンシブ対応）
    
    Args:
        image_file: 元画像ファイル
    
    Returns:
        dict: 各サイズの画像ファイル
    """
    sizes = {
        'thumbnail': (300, 300),
        'small': (600, 600),
        'medium': (1200, 1200),
        'large': (1920, 1920)
    }
    
    result = {}
    
    for size_name, (width, height) in sizes.items():
        try:
            image_file.seek(0)
            image = Image.open(image_file)
            
            # 現在のサイズ
            current_width, current_height = image.size
            
            # 指定サイズより小さい場合はスキップ
            if current_width <= width and current_height <= height and size_name != 'thumbnail':
                continue
            
            # RGBAモードの場合はRGBに変換
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # リサイズ
            image.thumbnail((width, height), Image.Resampling.LANCZOS)
            
            # 品質設定（サイズに応じて調整）
            quality = 90 if size_name == 'large' else 85 if size_name == 'medium' else 80
            
            # BytesIOに保存
            output = BytesIO()
            image.save(
                output, 
                format='JPEG', 
                quality=quality, 
                optimize=True,
                progressive=True
            )
            output.seek(0)
            
            # ファイル名生成
            original_name = os.path.splitext(image_file.name)[0]
            new_name = f"{original_name}_{size_name}.jpg"
            
            # InMemoryUploadedFileとして保存
            sized_file = InMemoryUploadedFile(
                output,
                None,
                new_name,
                'image/jpeg',
                output.getbuffer().nbytes,
                None
            )
            
            result[size_name] = sized_file
            
        except Exception as e:
            # 特定サイズの生成に失敗してもエラーにしない
            continue
    
    return result