/**
 * 高度な遅延読み込み機能
 * Intersection Observer APIを使用
 */

class LazyImageLoader {
    constructor() {
        this.imageObserver = null;
        this.init();
    }

    init() {
        // Intersection Observer APIがサポートされているかチェック
        if ('IntersectionObserver' in window) {
            this.setupIntersectionObserver();
        } else {
            // フォールバック: すべての画像を即座に読み込み
            this.loadAllImages();
        }
    }

    setupIntersectionObserver() {
        const options = {
            root: null, // ビューポートを使用
            rootMargin: '50px', // 50px手前で読み込み開始
            threshold: 0.1 // 10%見えたら読み込み
        };

        this.imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadImage(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, options);

        // 遅延読み込み対象の画像を監視
        this.observeImages();
    }

    observeImages() {
        const lazyImages = document.querySelectorAll('.lazy-image[data-src]');
        lazyImages.forEach(img => {
            this.imageObserver.observe(img);
        });
    }

    loadImage(img) {
        const src = img.dataset.src;
        if (!src) return;

        // 新しい画像オブジェクトを作成して事前読み込み
        const imageLoader = new Image();
        
        imageLoader.onload = () => {
            // 読み込み完了後に実際の画像に適用
            img.src = src;
            img.classList.remove('lazy-image');
            img.classList.add('loaded');
            
            // フェードイン効果
            img.style.opacity = '0';
            img.style.transition = 'opacity 0.3s ease-in-out';
            
            // 次のフレームで透明度を1に
            requestAnimationFrame(() => {
                img.style.opacity = '1';
            });
        };

        imageLoader.onerror = () => {
            // 読み込みエラー時の処理
            img.classList.add('error');
            img.alt = '画像の読み込みに失敗しました';
        };

        // 読み込み開始
        imageLoader.src = src;
    }

    loadAllImages() {
        // フォールバック: すべての遅延読み込み画像を即座に読み込み
        const lazyImages = document.querySelectorAll('.lazy-image[data-src]');
        lazyImages.forEach(img => {
            this.loadImage(img);
        });
    }

    // 新しい画像が動的に追加された場合の再初期化
    refresh() {
        if (this.imageObserver) {
            this.observeImages();
        }
    }
}

// プログレッシブ画像読み込み（低品質→高品質）
class ProgressiveImageLoader {
    constructor() {
        this.init();
    }

    init() {
        const progressiveImages = document.querySelectorAll('.progressive-image');
        progressiveImages.forEach(container => {
            this.loadProgressiveImage(container);
        });
    }

    loadProgressiveImage(container) {
        const lowQualityImg = container.querySelector('.low-quality');
        const highQualityImg = container.querySelector('.high-quality');
        
        if (!lowQualityImg || !highQualityImg) return;

        // 低品質画像を先に表示
        lowQualityImg.style.filter = 'blur(5px)';
        lowQualityImg.style.transition = 'filter 0.3s ease-in-out';

        // 高品質画像を事前読み込み
        const imageLoader = new Image();
        imageLoader.onload = () => {
            // 高品質画像の読み込み完了
            highQualityImg.src = imageLoader.src;
            highQualityImg.style.opacity = '0';
            highQualityImg.style.transition = 'opacity 0.5s ease-in-out';
            
            // フェードイン
            requestAnimationFrame(() => {
                highQualityImg.style.opacity = '1';
                lowQualityImg.style.filter = 'blur(0px)';
            });
        };

        imageLoader.src = highQualityImg.dataset.src;
    }
}

// 画像読み込み状況の監視
class ImageLoadingMonitor {
    constructor() {
        this.loadedImages = 0;
        this.totalImages = 0;
        this.init();
    }

    init() {
        this.totalImages = document.querySelectorAll('img').length;
        this.updateProgress();
        
        // 全画像の読み込み監視
        document.querySelectorAll('img').forEach(img => {
            if (img.complete) {
                this.onImageLoad();
            } else {
                img.addEventListener('load', () => this.onImageLoad());
                img.addEventListener('error', () => this.onImageLoad());
            }
        });
    }

    onImageLoad() {
        this.loadedImages++;
        this.updateProgress();
        
        if (this.loadedImages >= this.totalImages) {
            this.onAllImagesLoaded();
        }
    }

    updateProgress() {
        const progress = this.totalImages > 0 ? (this.loadedImages / this.totalImages) * 100 : 100;
        
        // カスタムイベントを発火
        document.dispatchEvent(new CustomEvent('imageLoadProgress', {
            detail: { progress, loaded: this.loadedImages, total: this.totalImages }
        }));
    }

    onAllImagesLoaded() {
        // 全画像読み込み完了イベント
        document.dispatchEvent(new CustomEvent('allImagesLoaded'));
        
        // ページ読み込み完了の視覚的フィードバック
        document.body.classList.add('images-loaded');
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    // 遅延読み込み初期化
    window.lazyImageLoader = new LazyImageLoader();
    
    // プログレッシブ読み込み初期化
    window.progressiveImageLoader = new ProgressiveImageLoader();
    
    // 読み込み監視初期化
    window.imageLoadingMonitor = new ImageLoadingMonitor();
});

// ページ遷移時の再初期化（SPA対応）
window.addEventListener('popstate', () => {
    if (window.lazyImageLoader) {
        window.lazyImageLoader.refresh();
    }
});

// 画像読み込み進捗の表示（オプション）
document.addEventListener('imageLoadProgress', (event) => {
    const { progress } = event.detail;
    
    // プログレスバーがある場合は更新
    const progressBar = document.querySelector('.image-loading-progress');
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
    }
});

// 全画像読み込み完了時の処理
document.addEventListener('allImagesLoaded', () => {
    // プログレスバーを非表示
    const progressBar = document.querySelector('.image-loading-progress');
    if (progressBar) {
        progressBar.style.display = 'none';
    }
    
    // アニメーション開始など
    document.body.classList.add('ready');
});