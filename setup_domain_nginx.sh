#!/bin/bash

# 🌐 ドメイン対応Nginx設定スクリプト

echo "🌐 ドメイン対応Nginx設定を開始します..."

# ドメイン対応Nginx設定作成
cat > nginx_touconnect_domain.conf << 'EOF'
server {
    listen 80;
    server_name touconnect.jp www.touconnect.jp;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

echo "✅ Nginx設定ファイル作成完了"

# VPSに転送
echo "📤 VPSに設定ファイルを転送中..."
scp -o ConnectTimeout=15 nginx_touconnect_domain.conf ike3don3@153.127.55.224:~/

# VPS上で設定適用
echo "🔧 VPS上でNginx設定を適用中..."
ssh -t ike3don3@153.127.55.224 "
sudo cp nginx_touconnect_domain.conf /etc/nginx/sites-available/touconnect
sudo nginx -t
sudo systemctl reload nginx
echo '✅ Nginx設定更新完了'
"

echo "🎉 ドメイン対応完了！"
echo "   アクセス先: http://touconnect.jp/"
echo "   ヘルスチェック: http://touconnect.jp/health"
