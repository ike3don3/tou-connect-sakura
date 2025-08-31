# 🚀 TOU Connect 本番デプロイ前チェックリスト

## 必須準備項目

### 🖥️ サーバー環境
- [ ] VPS/クラウドサーバーの準備完了
- [ ] Ubuntu 20.04+ または CentOS 8+ 
- [ ] 最低 2GB RAM, 20GB ディスク容量
- [ ] SSH アクセス設定完了
- [ ] sudo 権限のあるユーザーアカウント

### 🌐 ドメイン・ネットワーク
- [ ] ドメイン名の取得・設定
- [ ] DNS A レコードの設定
- [ ] ファイアウォール設定（ポート 80, 443, 22）
- [ ] SSL証明書の準備（Let's Encrypt推奨）

### 🗄️ データベース
- [ ] PostgreSQL サーバーの準備
- [ ] データベース名: `tou_connect_prod`
- [ ] データベースユーザー: `tou_connect`
- [ ] 強力なパスワードの設定
- [ ] バックアップ戦略の計画

### 🔄 キャッシュ・セッション
- [ ] Redis サーバーの準備
- [ ] Redis 設定の最適化
- [ ] メモリ制限の設定

### 🔐 セキュリティ・認証
- [ ] SECRET_KEY の生成（32文字以上のランダム文字列）
- [ ] Gemini API キーの取得
- [ ] Twitter Bearer Token の取得
- [ ] 環境変数の安全な管理方法の確立

### 📧 通知・監視
- [ ] SMTP サーバー設定（Gmail/SendGrid等）
- [ ] Slack Webhook URL（オプション）
- [ ] Sentry DSN（エラー監視、オプション）

## デプロイ実行手順

### 1. サーバー準備コマンド

```bash
# システム更新
sudo apt update && sudo apt upgrade -y

# 必要パッケージインストール
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server git curl

# PostgreSQL 設定
sudo -u postgres createuser --interactive tou_connect
sudo -u postgres createdb tou_connect_prod
sudo -u postgres psql -c "ALTER USER tou_connect PASSWORD 'YOUR_SECURE_PASSWORD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE tou_connect_prod TO tou_connect;"

# Redis 設定
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 2. アプリケーションデプロイ

```bash
# アプリケーションディレクトリ作成
sudo mkdir -p /opt/tou_connect
sudo chown $USER:$USER /opt/tou_connect

# ファイル転送（ローカルから実行）
scp -r tou_connect/ user@your-server:/opt/

# サーバーでの設定
cd /opt/tou_connect

# 環境設定ファイル作成
cp .env.production .env

# 以下の値を実際の値に変更
nano .env
```

### 3. 環境変数設定例

```bash
# 必須設定項目
SECRET_KEY=your-32-character-random-string-here
DATABASE_URL=postgresql://tou_connect:YOUR_PASSWORD@localhost:5432/tou_connect_prod
GEMINI_API_KEY=your-actual-gemini-api-key
TWITTER_BEARER_TOKEN=your-actual-twitter-token

# オプション設定
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SLACK_WEBHOOK_URL=your-slack-webhook-url
SENTRY_DSN=your-sentry-dsn
```

### 4. アプリケーション起動

```bash
# 仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements-production.txt

# データベース初期化
python3 init_database.py

# 権限設定
sudo chown -R www-data:www-data /opt/tou_connect

# Systemd サービス設定
sudo cp deployment/tou_connect.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tou_connect
sudo systemctl start tou_connect
```

### 5. Nginx 設定

```bash
# Nginx 設定ファイル
sudo cp nginx/tou_connect.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/tou_connect.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. SSL証明書設定

```bash
# Certbot インストール
sudo apt install certbot python3-certbot-nginx

# SSL証明書取得
sudo certbot --nginx -d your-domain.com

# 自動更新設定
sudo crontab -e
# 追加: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔍 デプロイ後確認項目

### 基本動作確認
- [ ] https://your-domain.com にアクセス可能
- [ ] ユーザー登録機能の動作
- [ ] ログイン機能の動作
- [ ] プロフィール分析機能の動作
- [ ] マッチング機能の動作

### パフォーマンス確認
- [ ] ページ読み込み速度 < 3秒
- [ ] データベース接続の安定性
- [ ] Redis キャッシュの動作
- [ ] 静的ファイルの配信

### セキュリティ確認
- [ ] HTTPS 強制リダイレクト
- [ ] セキュリティヘッダーの設定
- [ ] 不要なポートの閉鎖
- [ ] ファイル権限の適切な設定

### 監視・ログ確認
- [ ] アプリケーションログの出力
- [ ] エラーログの監視設定
- [ ] システムリソース監視
- [ ] バックアップの動作確認

## 🆘 トラブルシューティング

### よくある問題

1. **アプリケーションが起動しない**
   ```bash
   sudo journalctl -u tou_connect -f
   sudo systemctl status tou_connect
   ```

2. **データベース接続エラー**
   ```bash
   sudo systemctl status postgresql
   psql -h localhost -U tou_connect -d tou_connect_prod
   ```

3. **Nginx エラー**
   ```bash
   sudo nginx -t
   sudo tail -f /var/log/nginx/error.log
   ```

4. **SSL証明書の問題**
   ```bash
   sudo certbot certificates
   sudo certbot renew --dry-run
   ```

## 📞 緊急時連絡先

- システム管理者: [連絡先]
- 開発チーム: [連絡先]
- ホスティングプロバイダー: [連絡先]

## 📋 デプロイ完了報告

デプロイ完了後、以下の情報を記録してください：

- デプロイ日時: ___________
- サーバーIP: ___________
- ドメイン: ___________
- データベース接続確認: □
- SSL証明書確認: □
- 基本機能テスト完了: □
- 監視設定完了: □

---

**注意**: 本番環境では必ず事前にバックアップを取り、段階的にデプロイを行ってください。