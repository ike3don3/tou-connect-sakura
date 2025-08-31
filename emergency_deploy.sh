#!/bin/bash

# TOU Connect 緊急デプロイスクリプト
# シンプル版アプリケーションのデプロイ

set -e

echo "🚀 TOU Connect 緊急デプロイ開始"
echo "📅 $(date)"
echo "================================"

# 設定
VPS_IP="153.127.55.224"
VPS_USER="ike3don3"
APP_DIR="/home/ike3don3/touconnect"
DOMAIN="touconnect.jp"

# SSH接続テスト
echo "🔗 SSH接続テスト..."
if ssh -o ConnectTimeout=10 $VPS_USER@$VPS_IP "echo 'SSH接続成功'" > /dev/null 2>&1; then
    echo "✅ SSH接続成功"
else
    echo "❌ SSH接続失敗"
    echo "SSH設定を確認してください:"
    echo "1. SSH鍵の設定確認"
    echo "2. VPS IPアドレス確認: $VPS_IP"
    echo "3. ファイアウォール設定確認"
    exit 1
fi

# VPS上でのディレクトリ準備
echo "📁 デプロイディレクトリ準備..."
ssh $VPS_USER@$VPS_IP "
    mkdir -p $APP_DIR
    mkdir -p $APP_DIR/logs
    mkdir -p $APP_DIR/templates
    mkdir -p $APP_DIR/static
"

# ファイル転送
echo "📤 アプリケーションファイル転送..."
scp app_simple.py $VPS_USER@$VPS_IP:$APP_DIR/app.py
scp wsgi.py $VPS_USER@$VPS_IP:$APP_DIR/
scp requirements-simple.txt $VPS_USER@$VPS_IP:$APP_DIR/requirements.txt
scp -r templates/ $VPS_USER@$VPS_IP:$APP_DIR/
scp -r static/ $VPS_USER@$VPS_IP:$APP_DIR/

# .env.productionファイルが存在する場合は転送
if [ -f ".env.production" ]; then
    echo "📝 本番環境設定ファイル転送..."
    scp .env.production $VPS_USER@$VPS_IP:$APP_DIR/.env
fi

# VPS上でのセットアップ実行
echo "⚙️  VPS上でのアプリケーションセットアップ..."
ssh $VPS_USER@$VPS_IP "
    cd $APP_DIR
    
    # Python環境セットアップ
    if ! command -v python3 &> /dev/null; then
        echo '🐍 Python3インストール...'
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv
    fi
    
    # 仮想環境作成
    if [ ! -d 'venv' ]; then
        echo '📦 Python仮想環境作成...'
        python3 -m venv venv
    fi
    
    # 依存関係インストール
    echo '📥 依存関係インストール...'
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Nginx設定（簡易版）
    if ! command -v nginx &> /dev/null; then
        echo '🌐 Nginx インストール...'
        sudo apt install -y nginx
        apt install -y nginx
    fi
    
    # Nginxリバースプロキシ設定
    cat > /etc/nginx/sites-available/touconnect << 'EOF'
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static/ {
        alias $APP_DIR/static/;
        expires 1d;
        add_header Cache-Control \"public, immutable\";
    }
}
EOF
    
    # Nginx設定有効化
    ln -sf /etc/nginx/sites-available/touconnect /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
    
    # systemdサービス作成
    cat > /etc/systemd/system/touconnect.service << 'EOF'
[Unit]
Description=TOU Connect Flask Application
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
Environment=FLASK_ENV=production
Environment=ENVIRONMENT=production
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 120 wsgi:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    
    # 権限設定
    chown -R www-data:www-data $APP_DIR
    
    # サービス開始
    systemctl daemon-reload
    systemctl enable touconnect
    systemctl restart touconnect
    systemctl restart nginx
    
    echo '✅ デプロイ完了!'
"

# デプロイ後の確認
echo ""
echo "🔍 デプロイ確認..."
sleep 5

# ヘルスチェック
echo "⚕️  ヘルスチェック実行..."
if curl -f -s "http://$VPS_IP/health" > /dev/null; then
    echo "✅ アプリケーション正常稼働"
else
    echo "⚠️  ヘルスチェック失敗 - ログを確認してください"
fi

# DNS確認
echo "🌐 DNS確認..."
if nslookup $DOMAIN | grep -q "$VPS_IP"; then
    echo "✅ DNS設定正常"
else
    echo "⚠️  DNS設定を確認してください"
    echo "お名前.com管理画面で以下を設定:"
    echo "ホスト名: @ / TYPE: A / VALUE: $VPS_IP"
    echo "ホスト名: www / TYPE: A / VALUE: $VPS_IP"
fi

echo ""
echo "🎉 緊急デプロイ完了!"
echo "================================"
echo "🌐 URL: http://$DOMAIN (DNS反映後)"
echo "🌐 IP: http://$VPS_IP (即座にアクセス可能)"
echo "📊 ヘルスチェック: http://$DOMAIN/health"
echo "📡 API状態: http://$DOMAIN/api/status"
echo ""
echo "🔧 運用コマンド:"
echo "sudo systemctl status touconnect  # サービス状態確認"
echo "sudo systemctl restart touconnect # サービス再起動"
echo "sudo tail -f /var/log/nginx/access.log # アクセスログ"
echo ""
echo "📞 トラブルシューティング:"
echo "1. SSH接続: ssh $VPS_USER@$VPS_IP"
echo "2. ログ確認: sudo journalctl -u touconnect -f"
echo "3. Nginx確認: sudo nginx -t && sudo systemctl status nginx"
