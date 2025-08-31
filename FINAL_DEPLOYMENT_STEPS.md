# 🚀 TOU Connect 最終本番デプロイ手順

## 📋 デプロイ前の最終確認

### 1. 必要な情報の準備
- [ ] **サーバー情報**
  - サーバーIP: `_______________`
  - SSH接続情報: `ssh user@server-ip`
  - sudo権限の確認

- [ ] **ドメイン情報**
  - ドメイン名: `_______________`
  - DNS設定完了（A レコード）
  - ネームサーバー設定完了

- [ ] **API キー・認証情報**
  - Gemini API Key: `準備完了 □`
  - Twitter Bearer Token: `準備完了 □`
  - 強力なSECRET_KEY生成: `準備完了 □`

- [ ] **データベース情報**
  - PostgreSQL パスワード: `設定完了 □`
  - データベース名: `tou_connect_prod`
  - ユーザー名: `tou_connect`

## 🚀 デプロイ実行手順

### ステップ1: サーバーにファイルをアップロード

```bash
# ローカルマシンから実行
scp -r tou_connect/ user@YOUR_SERVER_IP:/tmp/

# サーバーにログイン
ssh user@YOUR_SERVER_IP

# ファイルを適切な場所に移動
sudo mkdir -p /opt/tou_connect
sudo mv /tmp/tou_connect/* /opt/tou_connect/
sudo chown -R $USER:$USER /opt/tou_connect
```

### ステップ2: 環境設定ファイルの編集

```bash
cd /opt/tou_connect

# 本番環境設定ファイルをコピー
cp .env.production .env

# 設定ファイルを編集
nano .env
```

**重要**: 以下の値を実際の値に変更してください：

```bash
# 必須変更項目
SECRET_KEY=YOUR_32_CHARACTER_RANDOM_STRING_HERE
DATABASE_URL=postgresql://tou_connect:YOUR_DB_PASSWORD@localhost:5432/tou_connect_prod
GEMINI_API_KEY=YOUR_ACTUAL_GEMINI_API_KEY
TWITTER_BEARER_TOKEN=YOUR_ACTUAL_TWITTER_TOKEN

# オプション項目
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### ステップ3: 自動デプロイスクリプト実行

```bash
# デプロイスクリプトに実行権限を付与
chmod +x deploy_production.sh

# ドメイン名を指定してデプロイ実行
sudo ./deploy_production.sh --domain YOUR_DOMAIN.com
```

### ステップ4: デプロイ完了確認

デプロイが完了したら、以下を確認してください：

```bash
# サービス状態確認
sudo systemctl status tou_connect
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis-server

# ログ確認
sudo journalctl -u tou_connect -f

# ヘルスチェック
curl -I https://YOUR_DOMAIN.com/health
```

## 🔧 手動デプロイ（自動スクリプトが使えない場合）

### 1. システム準備

```bash
# システム更新
sudo apt update && sudo apt upgrade -y

# 必要パッケージインストール
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server git curl

# PostgreSQL設定
sudo -u postgres createuser --interactive tou_connect
sudo -u postgres createdb tou_connect_prod
sudo -u postgres psql -c "ALTER USER tou_connect PASSWORD 'YOUR_SECURE_PASSWORD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE tou_connect_prod TO tou_connect;"

# Redis設定
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 2. アプリケーション設定

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

### 3. Nginx設定

```bash
# ドメイン名を置換してNginx設定ファイルを作成
sed "s/your-domain.com/YOUR_DOMAIN.com/g" deployment/nginx_production.conf | sudo tee /etc/nginx/sites-available/tou_connect

# サイト有効化
sudo ln -sf /etc/nginx/sites-available/tou_connect /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 設定テスト
sudo nginx -t

# Nginx再起動
sudo systemctl restart nginx
```

### 4. Systemdサービス設定

```bash
# サービスファイルコピー
sudo cp deployment/tou_connect.service /etc/systemd/system/

# サービス有効化・起動
sudo systemctl daemon-reload
sudo systemctl enable tou_connect
sudo systemctl start tou_connect
```

### 5. SSL証明書設定

```bash
# Certbotインストール
sudo apt install -y certbot python3-certbot-nginx

# SSL証明書取得
sudo certbot --nginx -d YOUR_DOMAIN.com -d www.YOUR_DOMAIN.com

# 自動更新設定
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

## 🔍 デプロイ後の確認項目

### 基本機能テスト

1. **Webサイトアクセス**
   ```bash
   curl -I https://YOUR_DOMAIN.com
   ```

2. **ヘルスチェック**
   ```bash
   curl https://YOUR_DOMAIN.com/health
   ```

3. **ユーザー登録テスト**
   - ブラウザでサイトにアクセス
   - 新規ユーザー登録を実行
   - プロフィール分析機能をテスト

### パフォーマンステスト

```bash
# 応答時間測定
curl -w "@curl-format.txt" -o /dev/null -s https://YOUR_DOMAIN.com

# 同時接続テスト（Apache Bench）
sudo apt install apache2-utils
ab -n 100 -c 10 https://YOUR_DOMAIN.com/
```

### セキュリティチェック

```bash
# SSL設定確認
curl -I https://YOUR_DOMAIN.com | grep -i security

# ポートスキャン
nmap YOUR_DOMAIN.com
```

## 🆘 トラブルシューティング

### よくある問題と解決方法

1. **アプリケーションが起動しない**
   ```bash
   # ログ確認
   sudo journalctl -u tou_connect -n 50
   
   # 設定ファイル確認
   cd /opt/tou_connect && source venv/bin/activate && python3 -c "from app_launch import app; print('OK')"
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
   sudo certbot renew
   ```

4. **Nginx設定エラー**
   ```bash
   # 設定テスト
   sudo nginx -t
   
   # エラーログ確認
   sudo tail -f /var/log/nginx/error.log
   ```

## 📊 監視・メンテナンス

### 定期メンテナンス項目

1. **日次**
   - アプリケーションログ確認
   - ディスク使用量確認
   - バックアップ確認

2. **週次**
   - セキュリティアップデート
   - パフォーマンス監視
   - エラーログ分析

3. **月次**
   - SSL証明書期限確認
   - データベース最適化
   - 不要ファイル削除

### 監視コマンド

```bash
# システムリソース監視
htop
df -h
free -h

# アプリケーション監視
sudo systemctl status tou_connect
curl https://YOUR_DOMAIN.com/health

# ログ監視
sudo tail -f /var/log/nginx/access.log
sudo journalctl -u tou_connect -f
```

## 🎉 デプロイ完了！

デプロイが正常に完了したら：

1. **アプリケーションURL**: `https://YOUR_DOMAIN.com`
2. **管理ダッシュボード**: `https://YOUR_DOMAIN.com/monitoring`
3. **ヘルスチェック**: `https://YOUR_DOMAIN.com/health`

### 次のステップ

- [ ] ユーザーテストの実施
- [ ] パフォーマンス監視の設定
- [ ] バックアップ戦略の確立
- [ ] 運用手順書の作成
- [ ] チーム向けトレーニングの実施

---

**🎯 おめでとうございます！TOU Connectが本番環境で稼働中です！**