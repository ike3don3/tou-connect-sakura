#!/bin/bash
# 完成版アプリ強制切り替え

echo "🔄 完成版アプリに強制切り替え..."

ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519 ike3don3@153.127.55.224 << 'EOSSH'

cd /home/ike3don3/apps/tou_connect
source venv/bin/activate

echo "🛑 全プロセス強制停止..."
pkill -9 -f "gunicorn" || true
pkill -9 -f "python.*8000" || true
pkill -9 -f "app_" || true
sleep 3

echo "🔍 プロセス確認..."
ps aux | grep -E "(gunicorn|python.*8000)" | grep -v grep || echo "全プロセス停止完了"

echo "🚀 完成版アプリ起動..."
export FLASK_APP=tou_connect_complete:app
nohup gunicorn --bind 127.0.0.1:8000 --workers 2 --timeout 120 tou_connect_complete:app > gunicorn.log 2>&1 &

sleep 5

echo "🔍 新プロセス確認..."
ps aux | grep -E "(gunicorn|tou_connect)" | grep -v grep

echo "🧪 完成版APIテスト..."
curl -s http://127.0.0.1:8000/health

echo "🎯 外部アクセステスト..."
curl -I https://touconnect.jp/

echo "✅ 完成版切り替え完了"

EOSSH

echo ""
echo "🌐 最終確認..."
curl -s https://touconnect.jp/health

echo ""
echo "🎉 TOU Connect 完成版サイト切り替え完了！"
echo "🌟 https://touconnect.jp"
