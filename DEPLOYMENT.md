# 写真共有サイト - 本番環境デプロイメントガイド

このドキュメントは写真共有サイトを本番環境にデプロイするための完全なガイドです。

## 前提条件

### システム要件
- Ubuntu 20.04 LTS または CentOS 8 以上
- Python 3.8 以上
- PostgreSQL 12 以上
- Redis 6 以上
- Nginx 1.18 以上
- 最低 2GB RAM、20GB ディスク容量

### 必要なソフトウェア
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib redis-server nginx git

# CentOS/RHEL
sudo dnf install -y python3 python3-pip postgresql postgresql-server redis nginx git
```

## 1. システム準備

### 1.1 ユーザー作成
```bash
# Webアプリケーション用ユーザー作成
sudo useradd -m -s /bin/bash www-data
sudo usermod -aG sudo www-data
```

### 1.2 ディレクトリ作成
```bash
# アプリケーションディレクトリ
sudo mkdir -p /var/www/photo_sharing
sudo chown www-data:www-data /var/www/photo_sharing

# ログディレクトリ
sudo mkdir -p /var/log/django /var/log/gunicorn /var/log/nginx
sudo chown www-data:www-data /var/log/django /var/log/gunicorn

# ランタイムディレクトリ
sudo mkdir -p /run/gunicorn
sudo chown www-data:www-data /run/gunicorn
```

## 2. データベース設定

### 2.1 PostgreSQL設定
```bash
# PostgreSQL開始
sudo systemctl start postgresql
sudo systemctl enable postgresql

# データベースとユーザー作成
sudo -u postgres psql
```

```sql
-- PostgreSQL内で実行
CREATE DATABASE photo_sharing_db;
CREATE USER photo_sharing_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE photo_sharing_db TO photo_sharing_user;
ALTER USER photo_sharing_user CREATEDB;
\q
```

### 2.2 Redis設定
```bash
# Redis開始
sudo systemctl start redis
sudo systemctl enable redis

# Redis設定確認
redis-cli ping
```

## 3. アプリケーションデプロイ

### 3.1 コード取得
```bash
# www-dataユーザーに切り替え
sudo su - www-data
cd /var/www/photo_sharing

# Gitリポジトリクローン（または手動アップロード）
git clone https://github.com/your-username/photo-sharing-site.git .
```

### 3.2 Python環境設定
```bash
# 仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 環境変数設定
```bash
# 本番環境用環境変数ファイル作成
cp .env.production.template .env.production

# 環境変数を編集（適切な値に変更）
nano .env.production
```

### 3.4 デプロイメント実行
```bash
# デプロイメントスクリプト実行
python deploy.py --full
```

## 4. Webサーバー設定

### 4.1 Nginx設定
```bash
# 設定ファイルコピー
sudo cp nginx.conf.template /etc/nginx/sites-available/photo_sharing

# 設定ファイル編集（ドメイン名等を変更）
sudo nano /etc/nginx/sites-available/photo_sharing

# サイト有効化
sudo ln -s /etc/nginx/sites-available/photo_sharing /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# 設定テスト
sudo nginx -t

# Nginx再起動
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 4.2 SSL証明書設定（Let's Encrypt）
```bash
# Certbot インストール
sudo apt install certbot python3-certbot-nginx

# SSL証明書取得
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 自動更新設定
sudo crontab -e
# 以下を追加:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 5. Gunicorn設定

### 5.1 Systemdサービス設定
```bash
# サービスファイルコピー
sudo cp photo-sharing.service /etc/systemd/system/
sudo cp photo-sharing.socket /etc/systemd/system/

# サービス有効化
sudo systemctl daemon-reload
sudo systemctl enable photo-sharing.socket
sudo systemctl start photo-sharing.socket

# 状態確認
sudo systemctl status photo-sharing.socket
```

## 6. セキュリティ設定

### 6.1 ファイアウォール設定
```bash
# UFW設定（Ubuntu）
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# または firewalld設定（CentOS）
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 6.2 ファイル権限設定
```bash
# アプリケーションファイル権限
sudo chown -R www-data:www-data /var/www/photo_sharing
sudo chmod -R 755 /var/www/photo_sharing
sudo chmod -R 644 /var/www/photo_sharing/media

# 実行可能ファイル権限
sudo chmod +x /var/www/photo_sharing/deploy.py
sudo chmod +x /var/www/photo_sharing/manage.py
```

## 7. 監視・ログ設定

### 7.1 ログローテーション設定
```bash
# logrotate設定作成
sudo nano /etc/logrotate.d/photo_sharing
```

```
/var/log/django/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload photo-sharing
    endscript
}

/var/log/gunicorn/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload photo-sharing
    endscript
}
```

### 7.2 システム監視設定
```bash
# システムリソース監視用スクリプト作成
sudo nano /usr/local/bin/photo_sharing_monitor.sh
```

```bash
#!/bin/bash
# 写真共有サイト監視スクリプト

# サービス状態チェック
systemctl is-active --quiet photo-sharing || echo "ERROR: photo-sharing service is down"
systemctl is-active --quiet nginx || echo "ERROR: nginx service is down"
systemctl is-active --quiet postgresql || echo "ERROR: postgresql service is down"
systemctl is-active --quiet redis || echo "ERROR: redis service is down"

# ディスク使用量チェック
DISK_USAGE=$(df /var/www/photo_sharing | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "WARNING: Disk usage is ${DISK_USAGE}%"
fi

# メモリ使用量チェック
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ $MEMORY_USAGE -gt 80 ]; then
    echo "WARNING: Memory usage is ${MEMORY_USAGE}%"
fi
```

```bash
# 実行権限付与
sudo chmod +x /usr/local/bin/photo_sharing_monitor.sh

# Cron設定
sudo crontab -e
# 以下を追加（5分毎に監視）:
# */5 * * * * /usr/local/bin/photo_sharing_monitor.sh >> /var/log/photo_sharing_monitor.log 2>&1
```

## 8. バックアップ設定

### 8.1 データベースバックアップ
```bash
# バックアップスクリプト作成
sudo nano /usr/local/bin/backup_photo_sharing.sh
```

```bash
#!/bin/bash
# 写真共有サイトバックアップスクリプト

BACKUP_DIR="/var/backups/photo_sharing"
DATE=$(date +%Y%m%d_%H%M%S)

# バックアップディレクトリ作成
mkdir -p $BACKUP_DIR

# データベースバックアップ
pg_dump -h localhost -U photo_sharing_user photo_sharing_db > $BACKUP_DIR/db_backup_$DATE.sql

# メディアファイルバックアップ
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz -C /var/www/photo_sharing media/

# 古いバックアップ削除（30日以上）
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
# 実行権限付与
sudo chmod +x /usr/local/bin/backup_photo_sharing.sh

# 日次バックアップ設定
sudo crontab -e
# 以下を追加（毎日午前2時にバックアップ）:
# 0 2 * * * /usr/local/bin/backup_photo_sharing.sh >> /var/log/backup.log 2>&1
```

## 9. パフォーマンス最適化

### 9.1 データベース最適化
```sql
-- PostgreSQL最適化設定
-- /etc/postgresql/12/main/postgresql.conf に追加

shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### 9.2 Redis最適化
```bash
# /etc/redis/redis.conf 設定
sudo nano /etc/redis/redis.conf
```

```
# メモリ設定
maxmemory 512mb
maxmemory-policy allkeys-lru

# 永続化設定
save 900 1
save 300 10
save 60 10000
```

## 10. トラブルシューティング

### 10.1 よくある問題

#### サービスが起動しない
```bash
# ログ確認
sudo journalctl -u photo-sharing -f
sudo tail -f /var/log/gunicorn/photo_sharing_error.log
```

#### 静的ファイルが表示されない
```bash
# 権限確認
ls -la /var/www/photo_sharing/staticfiles/
sudo chown -R www-data:www-data /var/www/photo_sharing/staticfiles/
```

#### データベース接続エラー
```bash
# PostgreSQL状態確認
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT version();"
```

### 10.2 ヘルスチェック
```bash
# アプリケーション動作確認
curl -I http://localhost/
curl -I https://yourdomain.com/

# サービス状態確認
sudo systemctl status photo-sharing
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis
```

## 11. メンテナンス

### 11.1 アプリケーション更新
```bash
# 新しいコードをデプロイ
cd /var/www/photo_sharing
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python deploy.py --migrate --static
sudo systemctl reload photo-sharing
```

### 11.2 定期メンテナンス
- 週次: ログファイル確認
- 月次: セキュリティアップデート適用
- 四半期: バックアップ復旧テスト
- 年次: SSL証明書更新確認

## 12. セキュリティチェックリスト

- [ ] ファイアウォール設定完了
- [ ] SSL証明書設定完了
- [ ] データベースパスワード強化
- [ ] 管理画面IP制限設定
- [ ] ログ監視設定完了
- [ ] バックアップ設定完了
- [ ] セキュリティヘッダー設定完了
- [ ] ファイル権限適切に設定
- [ ] 不要なサービス停止
- [ ] システムアップデート適用

## サポート

問題が発生した場合は、以下のログファイルを確認してください：

- アプリケーションログ: `/var/log/django/photo_sharing.log`
- Gunicornログ: `/var/log/gunicorn/photo_sharing_error.log`
- Nginxログ: `/var/log/nginx/photo_sharing_error.log`
- システムログ: `sudo journalctl -u photo-sharing`