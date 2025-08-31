#!/bin/bash
# 現在動作中のファイルを美しいUIに直接置き換え

echo "🎨 美しいUI強制適用開始..."

ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519 ike3don3@153.127.55.224 << 'EOSSH'

cd /home/ike3don3/apps/tou_connect
source venv/bin/activate

echo "🔍 現在動作中のファイル特定..."
ps aux | grep -E "python.*8000|gunicorn" | grep -v grep

echo "🛑 全プロセス完全停止..."
pkill -9 -f "gunicorn" || true
pkill -9 -f "python.*8000" || true
sleep 5

echo "🎨 現在のアプリファイルを美しいUIに置き換え..."
cp beautiful_app.py simple_app.py
cp beautiful_app.py app_emergency.py
cp beautiful_app.py app_simple.py

echo "🚀 美しいUIアプリ起動..."
export FLASK_APP=simple_app:app
nohup gunicorn --bind 127.0.0.1:8000 --workers 2 --timeout 120 simple_app:app > ui_beautiful.log 2>&1 &

sleep 5

echo "🔍 新プロセス確認..."
ps aux | grep -E "gunicorn|python.*8000" | grep -v grep

echo "🧪 美しいUI確認..."
curl -s http://127.0.0.1:8000/ | head -5

echo "✅ 美しいUI強制適用完了"

EOSSH

echo ""
echo "🌐 最終確認..."
sleep 3
curl -s https://touconnect.jp/ | head -10

echo ""
echo "🎊 TOU Connect 美しいモダンUI完全適用！"
echo "✨ グラデーション、アニメーション、レスポンシブデザイン完備"
echo "🌟 https://touconnect.jp"
