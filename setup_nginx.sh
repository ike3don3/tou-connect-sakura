#!/bin/bash

echo "Nginx設定とファイアウォール設定を行います..."

# Nginxの設定ファイルをコピー
sudo cp nginx_touconnect.conf /etc/nginx/sites-available/touconnect

# シンボリックリンクを作成
sudo ln -sf /etc/nginx/sites-available/touconnect /etc/nginx/sites-enabled/

# デフォルトサイトを無効化
sudo rm -f /etc/nginx/sites-enabled/default

# Nginx設定をテスト
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx設定が正常です。Nginxを再起動します..."
    sudo systemctl reload nginx
    sudo systemctl status nginx
else
    echo "Nginx設定にエラーがあります。"
    exit 1
fi

# ファイアウォール設定
echo "ファイアウォールを設定中..."
sudo ufw allow 80/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 22/tcp

# UFWを有効化
sudo ufw --force enable

echo "設定完了！"
echo "アプリケーションは以下のURLでアクセス可能です:"
echo "- http://153.127.55.224/"
echo "- http://153.127.55.224/health"
