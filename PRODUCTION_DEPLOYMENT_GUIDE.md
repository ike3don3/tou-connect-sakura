# TOU Connect 本番環境デプロイガイド

## 🚀 本番デプロイ手順

### 前提条件
- サーバー（VPS、クラウドインスタンス）
- ドメイン名
- SSL証明書
- PostgreSQL データベース
- Redis サーバー

### 1. サーバー準備

#### Ubuntu/Debian サーバーの場合
```bash
# システム更新
sudo apt update && sudo apt upgrade -y

# 必要なパッケージのインストール
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server

# Docker のインストール（オプション）
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 2. データベース設定

#### PostgreSQL セットアップ
```bash
# PostgreSQL ユーザー作成
sudo -u postgres createuser --interactive tou_connect

# データベース作成
sudo -u postgres createdb tou_connect_prod

# パスワード設定
sudo -u postgres psql
ALTER USER tou_connect PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE tou_connect_prod TO tou_connect;
\\q
```

### 3. Redis 設定
```bash
# Redis 設定ファイル編集
sudo nano /etc/redis/redis.conf

# 以下の設定を変更
maxmemory 256mb
maxmemory-policy allkeys-lru

# Redis 再起動
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### 4. アプリケーションデプロイ

#### ファイル転送
```bash
# サーバーにファイルをアップロード
scp -r tou_connect/ user@your-server:/opt/
```

#### 環境設定
```bash
# サーバーにログイン
ssh user@your-server

# アプリケーションディレクトリに移動
cd /opt/tou_connect

# 本番環境設定ファイルの編集
cp .env.production .env
nano .env

# 以下の値を実際の本番環境用に変更:
# SECRET_KEY=実際のランダムな文字列
# DATABASE_URL=postgresql://tou_connect:password@localhost:5432/tou_connect_prod
# GEMINI_API_KEY=実際のAPIキー
# TWITTER_BEARER_TOKEN=実際のトークン
```

#### 仮想環境とアプリケーション設定
```bash
# 仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements-production.txt

# データベース初期化
python3 init_database.py

# 静的ファイル最適化
python3 -c "from optimization.static_optimizer import StaticOptimizer; optimizer = StaticOptimizer(); optimizer.optimize_directory('static')"
```

### 5. Nginx 設定

#### Nginx 設定ファイル作成
```bash
sudo nano /etc/nginx/sites-available/tou_connect
```

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # HTTPS リダイレクト
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL 証明書
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    
    # SSL 設定
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # セキュリティヘッダー
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    
    # 静的ファイル
    location /static/ {
        alias /opt/tou_connect/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # アプリケーション
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # タイムアウト設定
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
```

#### Nginx 有効化
```bash
# サイト有効化
sudo ln -s /etc/nginx/sites-available/tou_connect /etc/nginx/sites-enabled/

# 設定テスト
sudo nginx -t

# Nginx 再起動
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 6. Systemd サービス設定

#### サービスファイル作成
```bash
sudo nano /etc/systemd/system/tou_connect.service
```

```ini
[Unit]
Description=TOU Connect Web Application
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/tou_connect
Environment=PATH=/opt/tou_connect/venv/bin
ExecStart=/opt/tou_connect/venv/bin/gunicorn --config gunicorn.conf.py app_launch:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### サービス有効化
```bash
# 権限設定
sudo chown -R www-data:www-data /opt/tou_connect

# サービス有効化
sudo systemctl daemon-reload
sudo systemctl enable tou_connect
sudo systemctl start tou_connect

# ステータス確認
sudo systemctl status tou_connect
```

### 7. SSL証明書設定（Let's Encrypt）

```bash
# Certbot インストール
sudo apt install certbot python3-certbot-nginx

# SSL証明書取得
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 自動更新設定
sudo crontab -e
# 以下を追加
0 12 * * * /usr/bin/certbot renew --quiet
```

### 8. 監視・ログ設定

#### ログローテーション
```bash
sudo nano /etc/logrotate.d/tou_connect
```

```
/opt/tou_connect/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload tou_connect
    endscript
}
```

### 9. ファイアウォール設定

```bash
# UFW 設定
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 10. 最終確認

```bash
# サービス状態確認
sudo systemctl status tou_connect nginx postgresql redis-server

# ログ確認
sudo journalctl -u tou_connect -f

# アプリケーションテスト
curl -I https://your-domain.com/health
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

1. **アプリケーションが起動しない**
   ```bash
   # ログ確認
   sudo journalctl -u tou_connect -n 50
   
   # 権限確認
   sudo chown -R www-data:www-data /opt/tou_connect
   ```

2. **データベース接続エラー**
   ```bash
   # PostgreSQL 状態確認
   sudo systemctl status postgresql
   
   # 接続テスト
   psql -h localhost -U tou_connect -d tou_connect_prod
   ```

3. **静的ファイルが表示されない**
   ```bash
   # Nginx 設定確認
   sudo nginx -t
   
   # 権限確認
   sudo chmod -R 755 /opt/tou_connect/static/
   ```

## 📊 監視・メンテナンス

### 定期メンテナンス
- データベースバックアップ（日次）
- ログファイルの確認（週次）
- セキュリティアップデート（月次）
- SSL証明書の更新確認（月次）

### 監視項目
- アプリケーション応答時間
- データベース接続状況
- ディスク使用量
- メモリ使用量
- CPU使用率

## 🚀 デプロイ完了後の確認事項

1. **機能テスト**
   - ユーザー登録・ログイン
   - プロフィール分析
   - マッチング機能
   - 学習リソース推薦

2. **パフォーマンステスト**
   - ページ読み込み速度
   - 同時接続数テスト
   - データベースクエリ性能

3. **セキュリティテスト**
   - SSL証明書の確認
   - セキュリティヘッダーの確認
   - 脆弱性スキャン

## 📞 サポー��

問題が発生した場合は、以下の情報を収集してサポートに連絡してください：

- エラーログ（`/opt/tou_connect/logs/`）
- システムログ（`sudo journalctl -u tou_connect`）
- サーバー情報（OS、メモリ、CPU）
- 実行した手順