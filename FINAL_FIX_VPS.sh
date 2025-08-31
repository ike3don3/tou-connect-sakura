#!/bin/bash

# 🚨 TOU Connect 最終修正コマンド
# VPSで直接実行してください

echo "🚨 TOU Connect 最終修正開始..."

# 1. アプリケーションディレクトリに移動
cd /home/ike3don3/apps/tou_connect 2>/dev/null || \
cd /home/ike3don3/tou_connect 2>/dev/null || \
cd /opt/tou_connect 2>/dev/null || {
    echo "❌ アプリケーションディレクトリが見つかりません"
    echo "📂 利用可能なディレクトリ:"
    find /home/ike3don3 -name "*tou*" -type d 2>/dev/null
    exit 1
}

echo "📂 現在のディレクトリ: $(pwd)"

# 2. 仮想環境起動
source venv/bin/activate 2>/dev/null || {
    echo "⚠️ 仮想環境を作成中..."
    python3 -m venv venv
    source venv/bin/activate
    pip install flask gunicorn python-dotenv tweepy
}

# 3. 既存プロセス停止
sudo pkill -f "gunicorn" 2>/dev/null || true
sudo pkill -f "app_simple" 2>/dev/null || true

# 4. 環境変数設定
export FLASK_ENV=production
export ENVIRONMENT=production

# 5. アプリケーション起動
echo "🚀 Gunicornを起動中..."
gunicorn --bind 127.0.0.1:8000 --workers 2 --timeout 30 --daemon \
         --access-logfile /tmp/gunicorn_access.log \
         --error-logfile /tmp/gunicorn_error.log \
         app_simple:app

# 6. プロセス確認
sleep 2
echo "📊 Gunicornプロセス確認:"
ps aux | grep gunicorn | grep -v grep

# 7. ローカル接続テスト
echo "🧪 ローカル接続テスト:"
curl -I http://127.0.0.1:8000/health

# 8. Nginx再起動
echo "🔄 Nginx再起動..."
sudo systemctl reload nginx

# 9. 最終確認
echo "✅ 最終確認:"
curl -I https://touconnect.jp/health

echo "🎉 修正完了！"
