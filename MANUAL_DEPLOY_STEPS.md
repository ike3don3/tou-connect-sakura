# 🚀 TOU Connect 手動デプロイ完了手順

## 📊 現在の状況
- ✅ ファイル転送完了 - アプリケーションファイルがVPSに転送済み
- ⚠️ Python環境設定が必要
- ⚠️ Systemdサービス設定が必要

## 🔧 VPS側で実行が必要な手順

以下のコマンドを**VPSに直接ログイン**して実行してください：

```bash
# 1. VPSにログイン
ssh ike3don3@153.127.55.224
```

### ステップ1: 必要パッケージのインストール
```bash
# Python仮想環境とその他必要パッケージ
sudo apt update
sudo apt install -y python3.12-venv python3-pip nginx git

# Node.js (必要に応じて)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
```

### ステップ2: Python仮想環境設定
```bash
cd /home/ike3don3/apps/tou_connect

# 仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install --upgrade pip
pip install -r requirements-production.txt
```

### ステップ3: 環境変数設定
```bash
# 環境変数ファイル作成
cp .env.production .env

# 必要に応じて編集（Gemini APIキーなど）
nano .env
```

### ステップ4: データベース初期化
```bash
# 仮想環境が有効な状態で実行
python init_database.py
```

### ステップ5: Systemdサービス設定
```bash
# サービスファイル作成
sudo tee /etc/systemd/system/touconnect.service > /dev/null << 'EOF'
[Unit]
Description=TOU Connect Gunicorn Application
After=network.target

[Service]
User=ike3don3
Group=ike3don3
WorkingDirectory=/home/ike3don3/apps/tou_connect
Environment="PATH=/home/ike3don3/apps/tou_connect/venv/bin"
ExecStart=/home/ike3don3/apps/tou_connect/venv/bin/gunicorn -c gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# サービス有効化・開始
sudo systemctl daemon-reload
sudo systemctl start touconnect
sudo systemctl enable touconnect
sudo systemctl status touconnect
```

### ステップ6: Nginx設定
```bash
# Nginx設定ファイル作成
sudo tee /etc/nginx/sites-available/touconnect > /dev/null << 'EOF'
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
        alias /home/ike3don3/apps/tou_connect/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Nginx設定有効化
sudo ln -s /etc/nginx/sites-available/touconnect /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### ステップ7: 動作確認
```bash
# サービス状態確認
sudo systemctl status touconnect
sudo systemctl status nginx

# ローカル接続確認
curl -I http://localhost:8000/health

# 外部接続確認（ローカルから実行）
curl -I http://153.127.55.224/health
```

## 🎯 成功判定

以下が全て確認できれば成功：
- [ ] `sudo systemctl status touconnect` が active (running)
- [ ] `curl http://localhost:8000/health` で200 OK
- [ ] `curl http://153.127.55.224/health` で200 OK（ローカルから）

## 📞 次のステップ

動作確認が完了したら：
1. DNS反映確認: `dig touconnect.jp`
2. SSL証明書設定: `sudo certbot --nginx -d touconnect.jp -d www.touconnect.jp`

---

**実行場所**: VPS (153.127.55.224)  
**ユーザー**: ike3don3  
**目標**: TOU Connect本番稼働開始
