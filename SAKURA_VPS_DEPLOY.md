# 🌸 さくらVPS デプロイガイド

## 📋 TOU Connect を一般公開する手順

現在TOU Connectは **動的Webアプリケーション** として完全に動作中です。
さくらVPSで一般公開するための完全ガイドです。

## 🎯 **さくらVPS が最適な理由**

### ✅ **技術的適合性**
- **Python Flask対応**: ✅ 完全対応
- **Gunicorn**: ✅ 高性能WSGI
- **PostgreSQL**: ✅ 本格DB対応
- **SSL対応**: ✅ Let's Encrypt簡単設定

### 💰 **コスト効率**
```
初期費用: 0円
月額料金: 580円〜 (1Gプラン)
年間コスト: 約7,000円 (破格！)
```

### 🎓 **学生向け特典**
- 教育割引あり
- 無料試用期間
- 学習用途サポート

## 🚀 **デプロイ手順（1時間で完了）**

### Step 1: さくらVPS契約 (10分)

1. **さくらVPS申し込み**
   - https://vps.sakura.ad.jp/
   - プラン: 1G (月580円) 推奨
   - OS: Ubuntu 22.04 LTS

2. **サーバー情報取得**
   ```
   IPアドレス: xxx.xxx.xxx.xxx
   root パスワード: (自動生成)
   ```

### Step 2: サーバー初期設定 (15分)

```bash
# SSH接続
ssh root@your-server-ip

# システム更新
apt update && apt upgrade -y

# 必要なパッケージインストール
apt install -y python3 python3-pip python3-venv nginx git certbot python3-certbot-nginx

# ユーザー作成
adduser touconnect
usermod -aG sudo touconnect
```

### Step 3: アプリケーションデプロイ (20分)

```bash
# ユーザー切り替え
su - touconnect

# プロジェクトアップロード（方法1: Git使用）
git clone your-repository.git
cd tou_connect

# または（方法2: ファイル転送）
# ローカルからscp/rsyncでファイル転送

# Python環境準備
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-production.txt

# データベース初期化
python3 -c "
from app_launch import init_simple_database
init_simple_database()
"

# 本番設定
cp .env.production .env
```

### Step 4: Nginx設定 (10分)

```bash
# Nginx設定ファイル作成
sudo nano /etc/nginx/sites-available/touconnect

# 設定内容
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/touconnect/tou_connect/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# サイト有効化
sudo ln -s /etc/nginx/sites-available/touconnect /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 5: SSL証明書設定 (5分)

```bash
# ドメイン設定後
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 自動更新設定
sudo crontab -e
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### Step 6: サービス起動 (5分)

```bash
# Systemdサービス作成
sudo nano /etc/systemd/system/touconnect.service

[Unit]
Description=TOU Connect Web Application
After=network.target

[Service]
Type=notify
User=touconnect
Group=touconnect
WorkingDirectory=/home/touconnect/tou_connect
Environment=PATH=/home/touconnect/tou_connect/venv/bin
ExecStart=/home/touconnect/tou_connect/venv/bin/gunicorn --config gunicorn.conf.py app_launch:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target

# サービス開始
sudo systemctl daemon-reload
sudo systemctl enable touconnect
sudo systemctl start touconnect
```

## 🌐 **ドメイン設定**

### 推奨ドメイン
- `touconnect.com` (理想)
- `tou-connect.org` 
- `touconnect.jp`

### DNS設定
```
A Record:
@ → your-server-ip
www → your-server-ip

例:
touconnect.com → 203.0.113.10
www.touconnect.com → 203.0.113.10
```

## 🔧 **自動デプロイスクリプト**

便利な自動デプロイスクリプトを作成済み：

```bash
# ローカルで実行
./deploy.sh production your-server-ip
```

このスクリプトが以下を自動実行：
- ファイル転送
- 依存関係インストール
- 設定ファイル更新
- サービス再起動

## 📊 **コスト試算**

### 初期費用
- **さくらVPS**: 0円 (初期費用無料)
- **ドメイン**: 年1,000円程度
- **合計**: 約1,000円

### 月額運用費
- **さくらVPS 1G**: 580円
- **ドメイン**: 約83円/月
- **合計**: 約663円/月

### 年間総額
**約8,000円** (破格の安さ！)

## 🎯 **パフォーマンス予想**

### さくらVPS 1Gプランで対応可能
- **同時接続**: 100人
- **日間PV**: 10,000PV
- **レスポンス**: 0.5秒以下
- **稼働率**: 99.9%

### スケールアップ時
```
2Gプラン (月1,738円)
→ 同時接続300人対応

4Gプラン (月3,520円) 
→ 同時接続1000人対応
```

## 🚀 **今すぐ始められます**

### 1時間でできること
1. **VPS契約**: 10分
2. **サーバー設定**: 30分
3. **アプリデプロイ**: 20分

### 今日中にできること
- ドメイン取得・設定
- SSL証明書設定
- 友人への告知

### 明日にはできること
- 学生コミュニティでの本格告知
- フィードバック収集開始
- 収益化開始

## 🎊 **一般公開準備完了！**

TOU Connect は **今すぐ一般公開可能** な状態です。

さくらVPSでのデプロイで、世界中の人がアクセスできるWebサービスになります！

---

**次のステップ**: さくらVPS申し込み → 1時間後に世界公開！ 🌍

*推定デプロイ時間: 1時間*  
*推定月額コスト: 663円*  
*推定到達ユーザー: 無制限* ✨
