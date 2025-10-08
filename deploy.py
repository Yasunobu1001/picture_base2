#!/usr/bin/env python3
"""
本番環境デプロイメントスクリプト

このスクリプトは写真共有サイトを本番環境にデプロイするための
自動化ツールです。

使用方法:
    python deploy.py --check          # デプロイ前チェック
    python deploy.py --migrate        # データベースマイグレーション
    python deploy.py --static         # 静的ファイル収集
    python deploy.py --full           # 完全デプロイ
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

class DeploymentManager:
    """デプロイメント管理クラス"""
    
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.venv_path = self.base_dir / 'venv'
        self.manage_py = self.base_dir / 'manage.py'
        
    def run_command(self, command, check=True):
        """コマンドを実行"""
        print(f"実行中: {command}")
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                check=check,
                capture_output=True,
                text=True
            )
            if result.stdout:
                print(result.stdout)
            return result
        except subprocess.CalledProcessError as e:
            print(f"エラー: {e}")
            if e.stderr:
                print(f"エラー詳細: {e.stderr}")
            if check:
                sys.exit(1)
            return e
    
    def activate_venv(self):
        """仮想環境をアクティベート"""
        if os.name == 'nt':  # Windows
            activate_script = self.venv_path / 'Scripts' / 'activate.bat'
            return f'"{activate_script}" && '
        else:  # Unix/Linux/macOS
            activate_script = self.venv_path / 'bin' / 'activate'
            return f'source "{activate_script}" && '
    
    def check_environment(self):
        """環境チェック"""
        print("=== 環境チェック ===")
        
        # Python バージョンチェック
        python_version = sys.version_info
        if python_version < (3, 8):
            print("エラー: Python 3.8以上が必要です")
            return False
        print(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # 仮想環境チェック
        if not self.venv_path.exists():
            print("エラー: 仮想環境が見つかりません")
            return False
        print("✓ 仮想環境")
        
        # manage.py チェック
        if not self.manage_py.exists():
            print("エラー: manage.py が見つかりません")
            return False
        print("✓ Django プロジェクト")
        
        # 必要な環境変数チェック
        required_env_vars = [
            'SECRET_KEY',
            'DATABASE_NAME',
            'DATABASE_USER',
            'DATABASE_PASSWORD',
            'ALLOWED_HOSTS'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"エラー: 以下の環境変数が設定されていません: {', '.join(missing_vars)}")
            return False
        print("✓ 環境変数")
        
        # データベース接続チェック
        activate_cmd = self.activate_venv()
        db_check = self.run_command(
            f'{activate_cmd}python "{self.manage_py}" check --database default --settings=photo_sharing_site.production_settings',
            check=False
        )
        if db_check.returncode != 0:
            print("警告: データベース接続に問題がある可能性があります")
        else:
            print("✓ データベース接続")
        
        print("環境チェック完了")
        return True
    
    def install_dependencies(self):
        """依存関係をインストール"""
        print("=== 依存関係インストール ===")
        activate_cmd = self.activate_venv()
        
        # pip アップグレード
        self.run_command(f'{activate_cmd}pip install --upgrade pip')
        
        # 依存関係インストール
        self.run_command(f'{activate_cmd}pip install -r requirements.txt')
        
        print("依存関係インストール完了")
    
    def run_migrations(self):
        """データベースマイグレーション実行"""
        print("=== データベースマイグレーション ===")
        activate_cmd = self.activate_venv()
        
        # マイグレーション確認
        self.run_command(
            f'{activate_cmd}python "{self.manage_py}" showmigrations --settings=photo_sharing_site.production_settings'
        )
        
        # マイグレーション実行
        self.run_command(
            f'{activate_cmd}python "{self.manage_py}" migrate --settings=photo_sharing_site.production_settings'
        )
        
        print("データベースマイグレーション完了")
    
    def collect_static_files(self):
        """静的ファイル収集"""
        print("=== 静的ファイル収集 ===")
        activate_cmd = self.activate_venv()
        
        # 静的ファイル収集
        self.run_command(
            f'{activate_cmd}python "{self.manage_py}" collectstatic --noinput --settings=photo_sharing_site.production_settings'
        )
        
        print("静的ファイル収集完了")
    
    def build_css(self):
        """CSS ビルド"""
        print("=== CSS ビルド ===")
        
        # Tailwind CSS ビルド
        if (self.base_dir / 'package.json').exists():
            self.run_command('npm run build-css-prod')
        else:
            print("警告: package.json が見つかりません。CSS ビルドをスキップします。")
        
        print("CSS ビルド完了")
    
    def run_tests(self):
        """テスト実行"""
        print("=== テスト実行 ===")
        activate_cmd = self.activate_venv()
        
        # テスト実行
        test_result = self.run_command(
            f'{activate_cmd}python "{self.manage_py}" test --settings=photo_sharing_site.test_settings',
            check=False
        )
        
        if test_result.returncode != 0:
            print("警告: テストが失敗しました")
            return False
        
        print("テスト実行完了")
        return True
    
    def create_superuser(self):
        """スーパーユーザー作成"""
        print("=== スーパーユーザー作成 ===")
        activate_cmd = self.activate_venv()
        
        # 既存のスーパーユーザーチェック
        check_result = self.run_command(
            f'{activate_cmd}python "{self.manage_py}" shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).exists())" --settings=photo_sharing_site.production_settings',
            check=False
        )
        
        if 'True' in check_result.stdout:
            print("スーパーユーザーは既に存在します")
            return
        
        print("スーパーユーザーを作成してください:")
        self.run_command(
            f'{activate_cmd}python "{self.manage_py}" createsuperuser --settings=photo_sharing_site.production_settings'
        )
        
        print("スーパーユーザー作成完了")
    
    def setup_directories(self):
        """必要なディレクトリを作成"""
        print("=== ディレクトリセットアップ ===")
        
        directories = [
            self.base_dir / 'staticfiles',
            self.base_dir / 'media',
            self.base_dir / 'media' / 'photos',
            self.base_dir / 'media' / 'thumbnails',
            self.base_dir / 'media' / 'profiles',
            Path('/var/log/django'),  # ログディレクトリ
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                print(f"✓ {directory}")
            except PermissionError:
                print(f"警告: {directory} の作成に失敗しました（権限不足）")
        
        print("ディレクトリセットアップ完了")
    
    def cleanup_development_files(self):
        """本番環境で不要な開発用ファイルを削除"""
        print("=== 開発用ファイルクリーンアップ ===")
        
        # 削除対象のファイル・ディレクトリ
        cleanup_targets = [
            # 開発・テスト用ファイル
            'verify_setup.py',
            'test_*.py',
            '*_test.py',
            '*.test.py',
            
            # Kiro IDE関連
            '.kiro/',
            
            # 開発用設定ファイル
            '.env.example',
            'local_settings.py',
            
            # テスト・カバレッジファイル
            '.coverage',
            'htmlcov/',
            '.pytest_cache/',
            
            # 一時ファイル
            '*.tmp',
            '*.temp',
            '*.bak',
            '*.backup',
            
            # IDE設定
            '.vscode/',
            '.idea/',
            
            # ログファイル（本番では別途管理）
            '*.log',
            
            # Node.js開発ファイル
            'node_modules/',
            'npm-debug.log*',
            
            # Python キャッシュ
            '__pycache__/',
            '*.pyc',
            '*.pyo',
        ]
        
        import glob
        import shutil
        
        removed_count = 0
        for pattern in cleanup_targets:
            matches = glob.glob(str(self.base_dir / pattern), recursive=True)
            for match in matches:
                try:
                    match_path = Path(match)
                    if match_path.is_file():
                        match_path.unlink()
                        print(f"削除: {match_path.relative_to(self.base_dir)}")
                        removed_count += 1
                    elif match_path.is_dir():
                        shutil.rmtree(match_path)
                        print(f"削除: {match_path.relative_to(self.base_dir)}/")
                        removed_count += 1
                except (OSError, PermissionError) as e:
                    print(f"警告: {match} の削除に失敗: {e}")
        
        print(f"クリーンアップ完了: {removed_count}個のファイル/ディレクトリを削除")
    
    def create_production_requirements(self):
        """本番用requirements.txtを作成"""
        print("=== 本番用requirements.txt作成 ===")
        
        # 開発用パッケージを除外した本番用requirements.txt
        production_packages = [
            'Django==4.2.24',
            'psycopg2-binary==2.9.9',
            'Pillow==10.1.0',
            'whitenoise==6.6.0',
            'python-decouple==3.8',
            'gunicorn==21.2.0',  # 本番用WSGIサーバー
            'psutil==5.9.6',     # システム監視用
        ]
        
        # 開発用パッケージ（本番では不要）
        development_packages = [
            'pytest',
            'pytest-django',
            'coverage',
            'factory-boy',
            'django-debug-toolbar',
            'ipython',
            'jupyter',
        ]
        
        requirements_prod_path = self.base_dir / 'requirements-production.txt'
        
        with open(requirements_prod_path, 'w', encoding='utf-8') as f:
            f.write("# 本番環境用パッケージ\n")
            f.write("# 開発・テスト用パッケージは除外済み\n\n")
            for package in production_packages:
                f.write(f"{package}\n")
        
        print(f"本番用requirements.txt作成完了: {requirements_prod_path}")
        return requirements_prod_path
    
    def full_deployment(self):
        """完全デプロイメント"""
        print("=== 完全デプロイメント開始 ===")
        
        # 環境チェック
        if not self.check_environment():
            print("環境チェックに失敗しました")
            return False
        
        # 本番用requirements.txt作成
        self.create_production_requirements()
        
        # ディレクトリセットアップ
        self.setup_directories()
        
        # 依存関係インストール
        self.install_dependencies()
        
        # CSS ビルド
        self.build_css()
        
        # データベースマイグレーション
        self.run_migrations()
        
        # 静的ファイル収集
        self.collect_static_files()
        
        # テスト実行（本番デプロイ前の最終確認）
        if not self.run_tests():
            print("警告: テストに失敗しましたが、デプロイを続行します")
        
        # 開発用ファイルクリーンアップ
        self.cleanup_development_files()
        
        # スーパーユーザー作成
        self.create_superuser()
        
        print("=== デプロイメント完了 ===")
        print("本番環境の準備が完了しました！")
        print("\n次のステップ:")
        print("1. Webサーバー（Nginx/Apache）の設定")
        print("2. WSGI サーバー（Gunicorn/uWSGI）の起動")
        print("3. SSL証明書の設定")
        print("4. ファイアウォールの設定")
        print("5. 監視・ログ設定の確認")
        print("\n本番用ファイル:")
        print("- requirements-production.txt: 本番用パッケージリスト")
        print("- 開発用ファイルは自動削除済み")
        
        return True


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='写真共有サイト デプロイメントスクリプト')
    parser.add_argument('--check', action='store_true', help='環境チェックのみ実行')
    parser.add_argument('--migrate', action='store_true', help='データベースマイグレーションのみ実行')
    parser.add_argument('--static', action='store_true', help='静的ファイル収集のみ実行')
    parser.add_argument('--test', action='store_true', help='テストのみ実行')
    parser.add_argument('--css', action='store_true', help='CSS ビルドのみ実行')
    parser.add_argument('--cleanup', action='store_true', help='開発用ファイルクリーンアップのみ実行')
    parser.add_argument('--full', action='store_true', help='完全デプロイメント実行')
    
    args = parser.parse_args()
    
    deployment = DeploymentManager()
    
    if args.check:
        deployment.check_environment()
    elif args.migrate:
        deployment.run_migrations()
    elif args.static:
        deployment.collect_static_files()
    elif args.test:
        deployment.run_tests()
    elif args.css:
        deployment.build_css()
    elif args.cleanup:
        deployment.cleanup_development_files()
    elif args.full:
        deployment.full_deployment()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()