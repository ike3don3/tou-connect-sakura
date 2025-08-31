#!/bin/bash

# 🚀 TOU Connect 自動復旧スクリプト
# 502エラーの自動修正を試行

echo "🚀 TOU Connect 自動復旧開始..."

DOMAIN="touconnect.jp"
IP="153.127.55.224"

# カラー設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. 現在のローカルアプリケーションを起動して代替サーバーとして使用
print_step "ローカル代替サーバーを準備中..."

# ローカルでアプリケーションを起動（ポート8080）
if ! pgrep -f "python.*app_simple" > /dev/null; then
    echo "ローカルアプリケーションを起動中..."
    cd /Users/kawakamimusashi/Desktop/summarizer/tou_connect
    source venv/bin/activate 2>/dev/null || true
    PORT=8080 python3 app_simple.py > /tmp/tou_connect_local.log 2>&1 &
    LOCAL_PID=$!
    sleep 3
    
    if curl -s http://localhost:8080/health > /dev/null; then
        print_success "ローカルアプリケーション起動成功 (PID: $LOCAL_PID)"
    else
        print_error "ローカルアプリケーション起動失敗"
    fi
else
    print_success "ローカルアプリケーションは既に稼働中"
fi

# 2. VPSの問題を特定するためのリモート診断
print_step "VPS問題診断中..."

# 502エラーの原因を特定
echo "502エラーの原因:"
echo "1. Flaskアプリケーションが停止している"
echo "2. Gunicornプロセスが起動していない" 
echo "3. ポート8000でリスニングしていない"
echo "4. Nginxのproxy_pass設定に問題がある"

# 3. 簡易的な修正コマンドセットを生成
print_step "修正コマンドセットを生成中..."

cat > /tmp/vps_fix_commands.txt << 'EOF'
# TOU Connect VPS 緊急修正コマンド
# 以下のコマンドをVPS (ike3don3@153.127.55.224) で順番に実行してください

echo "🔧 TOU Connect VPS 緊急修正開始"

# 1. 現在のプロセス確認
echo "=== 現在のプロセス状況 ==="
ps aux | grep -E "(gunicorn|python|nginx)" | grep -v grep

# 2. ポート使用状況確認
echo "=== ポート使用状況 ==="
sudo netstat -tlnp | grep -E ":80|:443|:8000"

# 3. アプリケーションディレクトリに移動
cd /home/ike3don3/apps/tou_connect || cd /home/ike3don3/tou_connect || cd /opt/tou_connect || {
    echo "❌ アプリケーションディレクトリが見つかりません"
    exit 1
}

echo "📂 現在のディレクトリ: $(pwd)"
ls -la

# 4. 既存プロセス停止
echo "🛑 既存プロセスを停止中..."
sudo pkill -f "gunicorn.*app" || true
sudo pkill -f "python.*app" || true

# 5. 仮想環境確認・起動
echo "🐍 Python環境準備中..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ 仮想環境アクティベート完了"
else
    echo "⚠️ 仮想環境を作成中..."
    python3 -m venv venv
    source venv/bin/activate
    pip install flask gunicorn python-dotenv tweepy
fi

# 6. 必要ファイル確認
echo "📁 アプリケーションファイル確認..."
if [ ! -f "app_simple.py" ]; then
    echo "❌ app_simple.py が見つかりません"
    ls -la *.py
    exit 1
fi

# 7. 環境変数設定
export FLASK_ENV=production
export ENVIRONMENT=production
export PORT=8000

# 8. アプリケーション起動
echo "🚀 アプリケーション起動中..."
gunicorn --bind 127.0.0.1:8000 --workers 2 --timeout 30 --daemon --access-logfile /tmp/gunicorn_access.log --error-logfile /tmp/gunicorn_error.log app_simple:app

# 9. プロセス確認
sleep 2
echo "=== アプリケーションプロセス確認 ==="
ps aux | grep gunicorn | grep -v grep

# 10. ローカル接続テスト
echo "🧪 ローカル接続テスト..."
curl -I http://127.0.0.1:8000/health

# 11. Nginx設定確認
echo "🌐 Nginx設定確認..."
sudo nginx -t

# 12. Nginx再起動
echo "🔄 Nginx再起動..."
sudo systemctl reload nginx

# 13. 最終確認
echo "✅ 修正完了 - 外部接続テスト"
curl -I http://localhost/health

echo "🎉 修正作業完了！"
echo "外部から https://touconnect.jp でアクセスを確認してください"
EOF

print_success "修正コマンドセット生成完了: /tmp/vps_fix_commands.txt"

# 4. 修正手順の表示
echo ""
echo -e "${YELLOW}🔧 緊急修正手順${NC}"
echo "========================="
echo ""
echo "1. VPSにSSH接続："
echo "   ssh ike3don3@153.127.55.224"
echo ""
echo "2. 修正コマンドを実行："
echo "   以下のファイルの内容を実行してください："
echo "   /tmp/vps_fix_commands.txt"
echo ""
echo "または、以下のコマンドを直接コピー&ペーストしてください："
echo ""

# コマンドを直接表示
cat /tmp/vps_fix_commands.txt | grep -v "^#" | grep -v "^$"

echo ""
echo -e "${GREEN}💡 修正のポイント${NC}"
echo "=================="
echo "1. Gunicornプロセスが127.0.0.1:8000で起動していることを確認"
echo "2. Nginxがproxy_passで正しく転送していることを確認"
echo "3. ファイアウォールでポート8000が内部アクセス可能であることを確認"
echo ""

# 5. 継続監視
print_step "5分後に自動再診断を実行します..."
echo "修正作業中にこのスクリプトは待機します..."

sleep 300  # 5分待機

echo ""
print_step "修正後の自動診断を実行中..."
./production_diagnostics.sh

echo ""
print_success "自動復旧スクリプト完了"
