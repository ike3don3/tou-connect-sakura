#!/bin/bash

# TOU Connect 本番環境デプロイスクリプト
# 使用方法: ./deploy.sh [environment]

set -e

# カラー出力設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 環境設定
ENVIRONMENT=${1:-production}
PROJECT_NAME="tou-connect"
DOMAIN="touconnect.com"
BACKUP_DIR="/var/backups/$PROJECT_NAME"
LOG_FILE="/var/log/$PROJECT_NAME/deploy.log"

echo -e "${BLUE}🚀 TOU Connect デプロイ開始 ($ENVIRONMENT)${NC}"

# ログ設定
mkdir -p $(dirname $LOG_FILE)
exec 1> >(tee -a $LOG_FILE)
exec 2> >(tee -a $LOG_FILE >&2)

# 前提条件チェック
check_prerequisites() {
    echo -e "${YELLOW}📋 前提条件をチェック中...${NC}"
    
    # Python 3.11+ チェック
    if ! python3 --version | grep -E "3\.(11|12)" > /dev/null; then
        echo -e "${RED}❌ Python 3.11+ が必要です${NC}"
        exit 1
    fi
    
    # Git チェック
    if ! command -v git &> /dev/null; then
        echo -e "${RED}❌ Git が必要です${NC}"
        exit 1
    fi
    
    # PostgreSQL チェック
    if ! command -v psql &> /dev/null; then
        echo -e "${YELLOW}⚠️ PostgreSQL クライアントが見つかりません${NC}"
    fi
    
    echo -e "${GREEN}✅ 前提条件チェック完了${NC}"
}

# バックアップ作成
create_backup() {
    echo -e "${YELLOW}💾 バックアップ作成中...${NC}"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"
    
    mkdir -p $BACKUP_PATH
    
    # データベースバックアップ
    if [ "$ENVIRONMENT" = "production" ]; then
        pg_dump $DATABASE_URL > "$BACKUP_PATH/database.sql" 2>/dev/null || echo "データベースバックアップをスキップ"
    fi
    
    # アプリケーションバックアップ
    if [ -d "/var/www/$PROJECT_NAME" ]; then
        cp -r "/var/www/$PROJECT_NAME" "$BACKUP_PATH/app"
    fi
    
    echo -e "${GREEN}✅ バックアップ完了: $BACKUP_PATH${NC}"
}

# 依存関係インストール
install_dependencies() {
    echo -e "${YELLOW}📦 依存関係インストール中...${NC}"
    
    # Python仮想環境作成
    python3 -m venv venv
    source venv/bin/activate
    
    # pip アップグレード
    pip install --upgrade pip
    
    # 依存関係インストール
    if [ "$ENVIRONMENT" = "production" ]; then
        pip install -r requirements-production.txt
    else
        pip install -r requirements.txt
    fi
    
    echo -e "${GREEN}✅ 依存関係インストール完了${NC}"
}

# 環境変数設定
setup_environment() {
    echo -e "${YELLOW}🔧 環境変数設定中...${NC}"
    
    # 環境変数ファイル作成
    cat > .env.production << EOF
# 本番環境設定
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)

# データベース設定
DATABASE_URL=postgresql://\${DB_USER}:\${DB_PASSWORD}@\${DB_HOST}:\${DB_PORT}/\${DB_NAME}

# API キー（手動設定必要）
GEMINI_API_KEY=your_gemini_api_key_here
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here

# Redis設定
REDIS_URL=redis://localhost:6379/0

# セキュリティ設定
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# ログ設定
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s %(levelname)s %(name)s: %(message)s

# 監視設定
MONITORING_ENABLED=True
METRICS_ENABLED=True

# CDN設定
CDN_ENABLED=True
CDN_BASE_URL=https://cdn.touconnect.com
EOF
    
    echo -e "${GREEN}✅ 環境変数設定完了${NC}"
    echo -e "${YELLOW}⚠️ .env.production ファイルの API キーを手動で設定してください${NC}"
}

# データベース初期化
setup_database() {
    echo -e "${YELLOW}🗄️ データベース初期化中...${NC}"
    
    source venv/bin/activate
    
    # データベーススキーマ作成
    python3 -c "
from database.production_database_manager import ProductionDatabaseManager
from database.schema_manager import SchemaManager
import os

db_url = os.getenv('DATABASE_URL', 'sqlite:///tou_connect.db')
db = ProductionDatabaseManager(db_url)
schema_manager = SchemaManager(db)
schema_manager.create_production_schema()
print('データベーススキーマ作成完了')
"
    
    echo -e "${GREEN}✅ データベース初期化完了${NC}"
}

# Nginxサーバー設定
setup_nginx() {
    echo -e "${YELLOW}🌐 Nginx設定中...${NC}"
    
    sudo tee /etc/nginx/sites-available/$PROJECT_NAME << EOF > /dev/null
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    root /var/www/$PROJECT_NAME;
    
    # セキュリティヘッダー
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static/ {
        alias /var/www/$PROJECT_NAME/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF
    
    # サイト有効化
    sudo ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
    
    # Nginx設定テスト
    sudo nginx -t
    
    echo -e "${GREEN}✅ Nginx設定完了${NC}"
}

# Systemdサービス設定
setup_systemd() {
    echo -e "${YELLOW}⚙️ Systemdサービス設定中...${NC}"
    
    sudo tee /etc/systemd/system/$PROJECT_NAME.service << EOF > /dev/null
[Unit]
Description=TOU Connect Web Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/$PROJECT_NAME
Environment=PATH=/var/www/$PROJECT_NAME/venv/bin
ExecStart=/var/www/$PROJECT_NAME/venv/bin/gunicorn --config gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=10
KillMode=mixed
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
EOF
    
    # サービス有効化
    sudo systemctl daemon-reload
    sudo systemctl enable $PROJECT_NAME
    
    echo -e "${GREEN}✅ Systemdサービス設定完了${NC}"
}

# SSL証明書設定
setup_ssl() {
    echo -e "${YELLOW}🔒 SSL証明書設定中...${NC}"
    
    # Certbot インストール確認
    if ! command -v certbot &> /dev/null; then
        echo -e "${YELLOW}Certbot をインストールしています...${NC}"
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
    fi
    
    # SSL証明書取得
    sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
    
    echo -e "${GREEN}✅ SSL証明書設定完了${NC}"
}

# サービス開始
start_services() {
    echo -e "${YELLOW}🚀 サービス開始中...${NC}"
    
    # アプリケーション開始
    sudo systemctl start $PROJECT_NAME
    sudo systemctl start nginx
    
    # 状態確認
    sleep 3
    if sudo systemctl is-active --quiet $PROJECT_NAME; then
        echo -e "${GREEN}✅ アプリケーション開始成功${NC}"
    else
        echo -e "${RED}❌ アプリケーション開始失敗${NC}"
        sudo systemctl status $PROJECT_NAME
        exit 1
    fi
    
    echo -e "${GREEN}✅ サービス開始完了${NC}"
}

# ヘルスチェック
health_check() {
    echo -e "${YELLOW}🏥 ヘルスチェック実行中...${NC}"
    
    # アプリケーションヘルスチェック
    if curl -f https://$DOMAIN/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ アプリケーション正常${NC}"
    else
        echo -e "${RED}❌ アプリケーション異常${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ ヘルスチェック完了${NC}"
}

# メイン実行
main() {
    echo -e "${BLUE}🎯 環境: $ENVIRONMENT${NC}"
    
    check_prerequisites
    create_backup
    install_dependencies
    setup_environment
    setup_database
    
    if [ "$ENVIRONMENT" = "production" ]; then
        setup_nginx
        setup_systemd
        setup_ssl
        start_services
        health_check
    fi
    
    echo -e "${GREEN}🎉 デプロイ完了！${NC}"
    echo -e "${BLUE}🌍 URL: https://$DOMAIN${NC}"
    echo -e "${YELLOW}📋 次のステップ:${NC}"
    echo -e "   1. .env.production ファイルの API キーを設定"
    echo -e "   2. ドメインの DNS 設定"
    echo -e "   3. モニタリング設定"
}

# 実行
main
