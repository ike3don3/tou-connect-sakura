# 🔧 TOU Connect 本番環境 手動修正ガイド

## 🚨 緊急修正手順

現在、SSH自動接続ができないため、以下の手順を**手動で実行**してください。

### 📋 事前確認
- VPS IP: 153.127.55.224
- ドメイン: touconnect.jp
- ユーザー: ike3don3

---

## 🔧 修正手順

### ステップ1: VPSにSSH接続
```bash
ssh ike3don3@153.127.55.224
```

### ステップ2: 現在の状況確認
```bash
# Nginx状態確認
sudo systemctl status nginx

# SSL証明書確認
sudo certbot certificates

# アプリケーションプロセス確認
ps aux | grep -E "(gunicorn|python.*app)"

# ディスク容量確認
df -h
```

### ステップ3: SSL証明書の修正
```bash
# SSL証明書の強制更新
sudo certbot --nginx -d touconnect.jp -d www.touconnect.jp --force-renewal

# 証明書の詳細確認
sudo certbot certificates
```

### ステップ4: TOU Connectアプリケーション修正
```bash
# アプリケーションディレクトリに移動
cd /home/ike3don3/apps/tou_connect || cd /home/ike3don3/tou_connect || cd /opt/tou_connect

# 既存プロセスの停止
sudo pkill -f "gunicorn.*app_simple" || true
sudo pkill -f "python.*app_simple" || true

# 仮想環境の確認・作成
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 環境変数設定
export FLASK_ENV=production
export ENVIRONMENT=production

# アプリケーション起動
gunicorn --bind 127.0.0.1:8000 --workers 2 --timeout 30 --daemon app_simple:app

# プロセス確認
ps aux | grep gunicorn
```

### ステップ5: Nginx設定確認・再起動
```bash
# Nginx設定テスト
sudo nginx -t

# Nginx設定確認
sudo cat /etc/nginx/sites-available/touconnect.jp

# Nginx再起動
sudo systemctl reload nginx
sudo systemctl status nginx
```

### ステップ6: ファイアウォール確認
```bash
# ファイアウォール状態確認
sudo ufw status

# 必要に応じて開放
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow ssh
```

---

## 🧪 動作確認

### ローカルテスト（VPS上で実行）
```bash
# ローカルアプリケーション確認
curl -I http://127.0.0.1:8000/health

# Nginx経由のテスト
curl -I http://localhost/health
```

### 外部からのテスト（ローカル環境で実行）
```bash
# HTTP接続テスト
curl -I http://touconnect.jp

# HTTPS接続テスト
curl -I https://touconnect.jp

# ヘルスチェック
curl https://touconnect.jp/health
```

---

## 🛠️ トラブルシューティング

### SSL証明書の問題
```bash
# 証明書の手動更新
sudo certbot renew --force-renewal

# 証明書のテスト
sudo certbot renew --dry-run
```

### アプリケーションが起動しない場合
```bash
# ログ確認
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# Python依存関係の確認
pip list

# ポート使用状況確認
sudo netstat -tlnp | grep :8000
```

### Nginx設定の問題
```bash
# 基本的なNginx設定の再作成
sudo tee /etc/nginx/sites-available/touconnect.jp << 'EOF'
server {
    listen 80;
    server_name touconnect.jp www.touconnect.jp;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name touconnect.jp www.touconnect.jp;

    ssl_certificate /etc/letsencrypt/live/touconnect.jp/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/touconnect.jp/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 設定の有効化
sudo ln -sf /etc/nginx/sites-available/touconnect.jp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## ✅ 修正完了の確認

以下がすべて成功すれば修正完了です：

1. **HTTPS接続**: https://touconnect.jp にアクセス可能
2. **ヘルスチェック**: https://touconnect.jp/health が正常レスポンス
3. **SSL証明書**: 有効な証明書でセキュア接続
4. **アプリケーション**: 全機能が正常動作

---

## 📞 サポート

修正後に問題が発生した場合は、以下の情報を含めてご報告ください：

1. 実行したコマンドとその結果
2. エラーメッセージ
3. ログファイルの内容（/var/log/nginx/error.log等）

**期待される最終状態**: https://touconnect.jp で TOU Connect が完全に動作すること
