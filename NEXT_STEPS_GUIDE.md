# 📝 次回作業時の手順書

## 🔍 **DNS反映確認**

### 1. DNS状況チェック
```bash
cd /Users/kawakamimusashi/Desktop/summarizer/tou_connect
./check_dns_status.sh
```

### 2. 手動確認 (オプション)
```bash
dig +short touconnect.jp A
dig +short www.touconnect.jp A
```

期待値: `153.127.55.224`

## 🔒 **DNS反映後のSSL設定**

### 1. ドメイン対応Nginx設定作成
```bash
# 新しい設定ファイル作成
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
```

### 2. 設定ファイル転送・適用
```bash
# VPSに転送
scp nginx_touconnect_domain.conf ike3don3@153.127.55.224:~/

# VPS上で設定適用
ssh -t ike3don3@153.127.55.224 "
sudo cp nginx_touconnect_domain.conf /etc/nginx/sites-available/touconnect
sudo nginx -t
sudo systemctl reload nginx
"
```

### 3. SSL証明書取得
```bash
ssh -t ike3don3@153.127.55.224 "
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d touconnect.jp -d www.touconnect.jp --email admin@touconnect.jp --agree-tos --non-interactive
"
```

### 4. 最終確認
```bash
# HTTPS接続確認
curl -I https://touconnect.jp/health
curl -I https://www.touconnect.jp/health

# SSL証明書確認
curl -I https://touconnect.jp
```

## 📱 **完成後のアクセスURL**
- **メインサイト**: https://touconnect.jp/
- **WWWサイト**: https://www.touconnect.jp/
- **ヘルスチェック**: https://touconnect.jp/health

## 🔧 **トラブルシューティング**

### DNS反映が遅い場合
```bash
# 異なるDNSサーバーで確認
dig @8.8.8.8 touconnect.jp A
dig @1.1.1.1 touconnect.jp A

# DNS キャッシュクリア (macOS)
sudo dscacheutil -flushcache
```

### SSL設定でエラーが出る場合
```bash
# Nginxログ確認
ssh ike3don3@153.127.55.224 "sudo tail -f /var/log/nginx/error.log"

# Certbotログ確認
ssh ike3don3@153.127.55.224 "sudo tail -f /var/log/letsencrypt/letsencrypt.log"
```

## 💾 **バックアップ**
重要ファイルは以下に保存済み:
- `PROJECT_STATUS_BACKUP_20250819.md` - 全体状況
- `DEPLOYMENT_CONFIG_BACKUP.md` - 設定情報
- `check_dns_status.sh` - DNS確認スクリプト

---
**最終更新**: 2025年8月19日 21:30
