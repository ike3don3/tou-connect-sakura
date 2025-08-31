# 🚀 さくらVPS本番デプロイ手順書

## 📋 前提条件確認
- ✅ さくらVPS契約完了
- ✅ ドメイン取得完了 (touconnect.jp)
- ✅ ローカル環境での動作確認完了

## 🔧 ステップ1: VPS初期設定

### 1.1 VPSへの接続
```bash
# さくらVPSの管理画面でIPアドレスを確認
# 初回ログイン（rootユーザー）
ssh root@[VPS_IP_ADDRESS]
```

### 1.2 システム更新
```bash
apt update && apt upgrade -y
```

### 1.3 作業用ユーザー作成
```bash
# 新しいユーザー作成
adduser touconnect
usermod -aG sudo touconnect

# SSH鍵の設定（推奨）
mkdir -p /home/touconnect/.ssh
cp /root/.ssh/authorized_keys /home/touconnect/.ssh/
chown -R touconnect:touconnect /home/touconnect/.ssh
chmod 700 /home/touconnect/.ssh
chmod 600 /home/touconnect/.ssh/authorized_keys
```

### 1.4 必要なソフトウェアインストール
```bash
# Python, Nginx, その他必要ツール
apt install -y python3 python3-venv python3-pip nginx git ufw htop

# Node.js (必要に応じて)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
apt install -y nodejs
```

## 🔐 ステップ2: セキュリティ設定

### 2.1 ファイアウォール設定
```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw enable
```

### 2.2 SSH設定強化
```bash
# /etc/ssh/sshd_config の編集
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart ssh
```

## 📁 ステップ3: アプリケーションデプロイ

### 3.1 作業ディレクトリ作成
```bash
# 作業用ユーザーに切り替え
su - touconnect

# アプリケーション用ディレクトリ
mkdir -p /home/touconnect/apps
cd /home/touconnect/apps
```

### 3.2 アプリケーションファイル転送
```bash
# ローカルから実行
scp -r /Users/kawakamimusashi/Desktop/summarizer/tou_connect/ touconnect@[VPS_IP]:/home/touconnect/apps/
```

### 3.3 Python仮想環境構築
```bash
cd /home/touconnect/apps/tou_connect
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements-production.txt
```

### 3.4 環境変数設定
```bash
# .env.production を .env にコピー
cp .env.production .env

# 必要に応じて本番用の値に調整
nano .env
```

### 3.5 データベース初期化
```bash
python init_database.py
```

## 🌐 ステップ4: Nginx設定

### 4.1 Nginx設定ファイル作成
```bash
sudo nano /etc/nginx/sites-available/touconnect
```

設定内容:
```nginx
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

    location /static/ {
        alias /home/touconnect/apps/tou_connect/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 4.2 Nginx設定有効化
```bash
sudo ln -s /etc/nginx/sites-available/touconnect /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔐 ステップ5: SSL証明書設定 (Let's Encrypt)

### 5.1 Certbot インストール
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 5.2 SSL証明書取得
```bash
sudo certbot --nginx -d touconnect.jp -d www.touconnect.jp
```

## 🔄 ステップ6: Systemdサービス設定

### 6.1 Systemdサービスファイル作成
```bash
sudo nano /etc/systemd/system/touconnect.service
```

設定内容:
```ini
[Unit]
Description=TOU Connect Gunicorn Application
After=network.target

[Service]
User=touconnect
Group=touconnect
WorkingDirectory=/home/touconnect/apps/tou_connect
Environment="PATH=/home/touconnect/apps/tou_connect/venv/bin"
ExecStart=/home/touconnect/apps/tou_connect/venv/bin/gunicorn -c gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

### 6.2 サービス開始・自動起動設定
```bash
sudo systemctl daemon-reload
sudo systemctl start touconnect
sudo systemctl enable touconnect
sudo systemctl status touconnect
```

## 🌍 ステップ7: DNS設定

### 7.1 お名前.comでAレコード設定
1. お名前.com管理画面にログイン
2. DNS設定/転送設定 → DNSレコード設定
3. 以下のAレコードを追加:
   - `@` → `[VPS_IP_ADDRESS]`
   - `www` → `[VPS_IP_ADDRESS]`

### 7.2 DNS反映確認
```bash
# ローカルで確認
dig touconnect.jp
dig www.touconnect.jp
nslookup touconnect.jp
```

## ✅ ステップ8: 最終動作確認

### 8.1 サービス状態確認
```bash
sudo systemctl status touconnect
sudo systemctl status nginx
curl -I http://localhost:8000/health
```

### 8.2 外部アクセス確認
```bash
curl -I https://touconnect.jp/health
curl -I https://www.touconnect.jp/health
```

### 8.3 ログ監視
```bash
# アプリケーションログ
tail -f /home/touconnect/apps/tou_connect/logs/app.log

# Systemdログ
sudo journalctl -u touconnect -f

# Nginxログ
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 🎉 完了！

一般公開URL: **https://touconnect.jp** 🚀

---

## 📞 トラブルシューティング

### よくある問題と解決方法

1. **502 Bad Gateway**
   - Gunicornが起動していない → `sudo systemctl start touconnect`
   - ポート設定の確認 → `netstat -tlnp | grep :8000`

2. **SSL証明書エラー**
   - Certbot再実行 → `sudo certbot renew --dry-run`

3. **DNS反映遅延**
   - 最大48時間かかる場合がある
   - CloudflareのDNSチェッカーで確認

4. **パフォーマンス問題**
   - Gunicornワーカー数調整 → `gunicorn.conf.py`
   - Nginxキャッシュ設定

---

**作成日**: 2025年8月17日  
**対象**: さくらVPS + お名前.comドメイン  
**ステータス**: 実行準備完了 ✅
