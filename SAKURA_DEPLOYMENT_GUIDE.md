# 🚀 TOU Connect さくらのVPS デプロイガイド

## 📋 サーバー情報
- **ドメイン**: touconnect.jp
- **ホスト名**: ik1-425-44970.vs.sakura.ne.jp
- **IPv4**: 153.127.55.224
- **IPv6**: 2401:2500:204:1125:153:127:55:224

## 🎯 デプロイ手順

### 前提条件
- [ ] さくらのVPSサーバーへのSSHアクセス
- [ ] sudo権限のあるユーザーアカウント
- [ ] ドメイン `touconnect.jp` のDNS設定完了
- [ ] Gemini API キーの取得
- [ ] Twitter Bearer Token の取得

### ステップ1: ローカルからサーバーへファイル転送

```bash
# ローカルマシンから実行
scp -r tou_connect/ user@153.127.55.224:/tmp/

# または、ホスト名を使用
scp -r tou_connect/ user@ik1-425-44970.vs.sakura.ne.jp:/tmp/
```

### ステップ2: サーバーにログインしてファイル配置

```bash
# サーバーにSSH接続
ssh user@153.127.55.224

# ファイルを適切な場所に移動
sudo mkdir -p /opt/tou_connect
sudo mv /tmp/tou_connect/* /opt/tou_connect/
sudo chown -R $USER:$USER /opt/tou_connect
cd /opt/tou_connect
```

### ステップ3: 環境設定ファイルの準備

```bash
# さくらのVPS用設定ファイルをコピー
cp .env.sakura .env

# 設定ファイルを編集（重要！）
nano .env
```

**必須変更項目**:
```bash
# 以下の値を実際の値に変更してください
GEMINI_API_KEY=YOUR_ACTUAL_GEMINI_API_KEY_HERE
TWITTER_BEARER_TOKEN=YOUR_ACTUAL_TWITTER_BEARER_TOKEN_HERE

# メール設定（Gmail使用例）
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
```

### ステップ4: 自動デプロイ実行

```bash
# デプロイスクリプトに実行権限を付与
chmod +x deploy_sakura.sh

# 自動デプロイ実行
sudo ./deploy_sakura.sh
```

### ステップ5: デプロイ完了確認

```bash
# サービス状態確認
sudo systemctl status tou_connect
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis-server

# ヘルスチェック
curl -I https://touconnect.jp/health

# ログ確認
sudo journalctl -u tou_connect -f
```

## 🔧 手動デプロイ（トラブル時）

### 1. システム準備

```bash
# システム更新
sudo apt update && sudo apt upgrade -y

# 必要パッケージインストール
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server git curl ufw

# ファイアウォール設定
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

### 2. PostgreSQL設定

```bash
# PostgreSQL起動・有効化
sudo systemctl enable postgresql
sudo systemctl start postgresql

# データベースとユーザー作成
sudo -u postgres psql -c "CREATE USER tou_connect WITH PASSWORD 'TouConnect2024!Sakura';"
sudo -u postgres psql -c "CREATE DATABASE tou_connect_prod OWNER tou_connect;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE tou_connect_prod TO tou_connect;"

# 接続テスト
psql -h localhost -U tou_connect -d tou_connect_prod
```

### 3. Redis設定

```bash
# Redis起動・有効化
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Redis設定調整
sudo nano /etc/redis/redis.conf
# 以下を追加/変更:
# maxmemory 256mb
# maxmemory-policy allkeys-lru

sudo systemctl restart redis-server
```

### 4. アプリケーション設定

```bash
cd /opt/tou_connect

# 仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install --upgrade pip
pip install -r requirements-production.txt

# データベース初期化
python3 init_database.py

# 静的ファイル最適化
python3 -c "
from optimization.static_optimizer import StaticOptimizer
optimizer = StaticOptimizer()
optimizer.optimize_directory('static')
"

# 権限設定
sudo chown -R www-data:www-data /opt/tou_connect
```

### 5. Nginx設定

```bash
# Nginx設定ファイル配置
sudo cp deployment/nginx_sakura.conf /etc/nginx/sites-available/tou_connect

# サイト有効化
sudo ln -sf /etc/nginx/sites-available/tou_connect /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 設定テスト
sudo nginx -t

# Nginx再起動
sudo systemctl restart nginx
```

### 6. SSL証明書設定

```bash
# Certbotインストール
sudo apt install -y certbot python3-certbot-nginx

# SSL証明書取得
sudo certbot --nginx -d touconnect.jp -d www.touconnect.jp

# 自動更新設定
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### 7. Systemdサービス設定

```bash
# サービスファイル配置
sudo cp deployment/tou_connect.service /etc/systemd/system/

# サービス有効化・起動
sudo systemctl daemon-reload
sudo systemctl enable tou_connect
sudo systemctl start tou_connect
```

## 🔍 動作確認

### 基本機能テスト

1. **Webサイトアクセス**
   ```bash
   curl -I https://touconnect.jp
   ```

2. **ヘルスチェック**
   ```bash
   curl https://touconnect.jp/health
   ```

3. **ブラウザテスト**
   - https://touconnect.jp にアクセス
   - ユーザー登録機能をテスト
   - プロフィール分析機能をテスト
   - マッチング機能をテスト

### パフォーマンステスト

```bash
# 応答時間測定
curl -w "時間: %{time_total}s\n" -o /dev/null -s https://touconnect.jp

# 同時接続テスト
sudo apt install apache2-utils
ab -n 100 -c 10 https://touconnect.jp/
```

## 🆘 トラブルシューティング

### よくある問題

1. **アプリケーションが起動しない**
   ```bash
   # ログ確認
   sudo journalctl -u tou_connect -n 50
   
   # 設定確認
   cd /opt/tou_connect
   source venv/bin/activate
   python3 -c "from app_launch import app; print('設定OK')"
   ```

2. **データベース接続エラー**
   ```bash
   # PostgreSQL状態確認
   sudo systemctl status postgresql
   
   # 接続テスト
   psql -h localhost -U tou_connect -d tou_connect_prod
   ```

3. **SSL証明書エラー**
   ```bash
   # 証明書確認
   sudo certbot certificates
   
   # 手動更新
   sudo certbot renew --dry-run
   ```

4. **Nginx設定エラー**
   ```bash
   # 設定テスト
   sudo nginx -t
   
   # エラーログ確認
   sudo tail -f /var/log/nginx/error.log
   ```

### ログファイル場所

- **アプリケーションログ**: `/opt/tou_connect/logs/app.log`
- **Nginxアクセスログ**: `/var/log/nginx/touconnect_access.log`
- **Nginxエラーログ**: `/var/log/nginx/touconnect_error.log`
- **システムログ**: `journalctl -u tou_connect`
- **デプロイログ**: `/var/log/tou_connect_deploy.log`

## 📊 監視・メンテナンス

### 日次チェック項目

```bash
# サービス状態確認
sudo systemctl status tou_connect nginx postgresql redis-server

# ディスク使用量確認
df -h

# メモリ使用量確認
free -h

# ヘルスチェック
curl https://touconnect.jp/health
```

### 週次メンテナンス

```bash
# システム更新
sudo apt update && sudo apt upgrade -y

# ログローテーション確認
sudo logrotate -f /etc/logrotate.conf

# SSL証明書期限確認
sudo certbot certificates
```

### 月次メンテナンス

```bash
# データベース最適化
sudo -u postgres psql -d tou_connect_prod -c "VACUUM ANALYZE;"

# 不要ファイル削除
sudo apt autoremove -y
sudo apt autoclean

# バックアップ確認
ls -la /opt/backups/tou_connect/
```

## 🎉 デプロイ完了！

デプロイが正常に完了したら：

- **メインサイト**: https://touconnect.jp
- **ヘルスチェック**: https://touconnect.jp/health
- **監視ダッシュボード**: https://touconnect.jp/monitoring

### 次のステップ

1. **API キーの設定確認**
2. **基本機能の動作テスト**
3. **パフォーマンス監視の設定**
4. **定期バックアップの設定**
5. **運用手順書の作成**

---

**🎯 おめでとうございます！TOU ConnectがさくらのVPSで稼働中です！**