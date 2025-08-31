#!/bin/bash

# Nginx設定ファイルを作成してデプロイするスクリプト

# 設定ファイルの内容を作成
cat > touconnect_nginx.conf << 'EOF'
server {
    listen 80;
    server_name 153.127.55.224;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静的ファイル
    location /static {
        alias /home/ike3don3/touconnect/static;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }

    # ヘルスチェック
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

echo "Nginx設定ファイルが作成されました: touconnect_nginx.conf"
echo "これをVPSに転送してください。"
