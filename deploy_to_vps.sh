#!/bin/bash

# 🚀 TOU Connect VPS自動デプロイスクリプト
# Usage: ./deploy_to_vps.sh [VPS_IP_ADDRESS]

set -e  # エラー時に停止

# カラー設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 設定
VPS_IP=${1:-""}
VPS_USER="ike3don3"  # さくらVPSで作成したユーザー
APP_NAME="tou_connect"
REMOTE_DIR="/home/$VPS_USER/apps"
LOCAL_DIR="$(pwd)"

# 関数定義
print_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# VPS IPアドレスチェック
if [ -z "$VPS_IP" ]; then
    print_error "VPS IPアドレスが指定されていません"
    echo "Usage: $0 [VPS_IP_ADDRESS]"
    exit 1
fi

echo -e "${BLUE}"
echo "============================================"
echo "🚀 TOU Connect VPS デプロイ開始"
echo "============================================"
echo -e "${NC}"
echo "VPS IP: $VPS_IP"
echo "ユーザー: $VPS_USER"
echo "アプリ名: $APP_NAME"
echo ""

# 接続テスト
print_step "VPS接続テスト"
if ssh -o ConnectTimeout=10 -o BatchMode=yes $VPS_USER@$VPS_IP exit 2>/dev/null; then
    print_success "VPS接続成功"
else
    print_error "VPS接続失敗。SSH設定を確認してください"
    exit 1
fi

# ローカルファイル準備
print_step "ローカルファイル準備"
if [ ! -f "requirements-production.txt" ]; then
    print_error "requirements-production.txt が見つかりません"
    exit 1
fi

if [ ! -f "gunicorn.conf.py" ]; then
    print_error "gunicorn.conf.py が見つかりません"
    exit 1
fi

print_success "ローカルファイル確認完了"

# ファイル転送前のバックアップ
print_step "リモートバックアップ作成"
ssh $VPS_USER@$VPS_IP "
    if [ -d $REMOTE_DIR/$APP_NAME ]; then
        cp -r $REMOTE_DIR/$APP_NAME $REMOTE_DIR/${APP_NAME}_backup_\$(date +%Y%m%d_%H%M%S)
    fi
"
print_success "バックアップ作成完了"

# アプリケーションファイル転送
print_step "アプリケーションファイル転送"
ssh $VPS_USER@$VPS_IP "mkdir -p $REMOTE_DIR"

# 除外ファイルを指定してrsync
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='tou_connect.db' \
    --exclude='logs/*.log' \
    --exclude='cache/*' \
    --exclude='backups/*' \
    $LOCAL_DIR/ $VPS_USER@$VPS_IP:$REMOTE_DIR/$APP_NAME/

print_success "ファイル転送完了"

# リモートでのセットアップ
print_step "リモートセットアップ実行"
ssh $VPS_USER@$VPS_IP "
    cd $REMOTE_DIR/$APP_NAME
    
    # Python仮想環境作成・有効化
    if [ ! -d 'venv' ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    
    # 依存関係インストール
    pip install --upgrade pip
    pip install -r requirements-production.txt
    
    # 環境変数設定
    if [ ! -f '.env' ]; then
        cp .env.production .env
        echo '環境変数ファイル (.env) を確認・編集してください'
    fi
    
    # データベース初期化
    python init_database.py
    
    # ディレクトリ権限設定
    chmod +x *.py
    
    echo 'リモートセットアップ完了'
"
print_success "リモートセットアップ完了"

# Systemdサービス設定
print_step "Systemdサービス設定"
ssh $VPS_USER@$VPS_IP "
    sudo tee /etc/systemd/system/touconnect.service > /dev/null << 'EOF'
[Unit]
Description=TOU Connect Gunicorn Application
After=network.target

[Service]
User=$VPS_USER
Group=$VPS_USER
WorkingDirectory=$REMOTE_DIR/$APP_NAME
Environment=\"PATH=$REMOTE_DIR/$APP_NAME/venv/bin\"
ExecStart=$REMOTE_DIR/$APP_NAME/venv/bin/gunicorn -c gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    # サービス再読み込み・再起動
    sudo systemctl daemon-reload
    sudo systemctl restart touconnect
    sudo systemctl enable touconnect
"
print_success "Systemdサービス設定完了"

# Nginx設定（必要に応じて）
print_step "Nginx設定チェック"
ssh $VPS_USER@$VPS_IP "
    if [ ! -f '/etc/nginx/sites-available/touconnect' ]; then
        sudo tee /etc/nginx/sites-available/touconnect > /dev/null << 'EOF'
server {
    listen 80;
    server_name touconnect.jp www.touconnect.jp;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias $REMOTE_DIR/$APP_NAME/static/;
        expires 30d;
        add_header Cache-Control \"public, immutable\";
    }
}
EOF
        
        sudo ln -sf /etc/nginx/sites-available/touconnect /etc/nginx/sites-enabled/
        sudo nginx -t && sudo systemctl reload nginx
        echo 'Nginx設定を作成・適用しました'
    else
        echo 'Nginx設定は既に存在します'
    fi
"
print_success "Nginx設定チェック完了"

# サービス状態確認
print_step "サービス状態確認"
ssh $VPS_USER@$VPS_IP "
    echo '=== TOU Connect サービス状態 ==='
    sudo systemctl status touconnect --no-pager -l
    
    echo '=== Nginx サービス状態 ==='
    sudo systemctl status nginx --no-pager -l
    
    echo '=== ポート確認 ==='
    sudo netstat -tlnp | grep :8000 || echo 'ポート8000が見つかりません'
    
    echo '=== ヘルスチェック ==='
    curl -s -I http://localhost:8000/health || echo 'ヘルスチェック失敗'
"

# デプロイ完了
echo ""
echo -e "${GREEN}"
echo "============================================"
echo "🎉 TOU Connect デプロイ完了！"
echo "============================================"
echo -e "${NC}"
echo "VPS IP: $VPS_IP"
echo "URL: https://touconnect.jp"
echo ""
print_success "デプロイ成功！次のステップ:"
echo "1. DNS設定確認 (Aレコード: @ → $VPS_IP, www → $VPS_IP)"
echo "2. SSL証明書設定: sudo certbot --nginx -d touconnect.jp -d www.touconnect.jp"
echo "3. 動作確認: curl -I https://touconnect.jp/health"
echo ""
print_warning "環境変数 (.env) の確認・編集を忘れずに！"

exit 0
