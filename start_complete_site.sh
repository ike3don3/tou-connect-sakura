#!/bin/bash
# VPS上で完成版を起動

echo "🚀 VPS上で完成版TOU Connectを起動..."

ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519 ike3don3@153.127.55.224 << 'EOSSH'

cd /home/ike3don3/apps/tou_connect
source venv/bin/activate

echo "🛑 既存プロセス停止..."
sudo pkill -9 -f "gunicorn" || true
sudo pkill -9 -f "python.*8000" || true
sleep 3

echo "🔧 権限設定..."
chmod +x tou_connect_complete.py

echo "🧪 アプリテスト..."
python3 -c "
import sys
sys.path.insert(0, '.')
import tou_connect_complete
print('✅ アプリ正常ロード完了')
"

echo "🚀 Gunicorn起動..."
export FLASK_APP=tou_connect_complete:app
gunicorn --bind 127.0.0.1:8000 --workers 2 --timeout 120 --daemon tou_connect_complete:app

sleep 5

echo "🔍 プロセス確認..."
ps aux | grep -E "(gunicorn|tou_connect)" | grep -v grep

echo "🔍 ポート確認..."
netstat -tulpn | grep 8000

echo "🧪 ローカルテスト..."
curl -s http://127.0.0.1:8000/health

echo "🔄 Nginx再起動..."
sudo systemctl reload nginx

sleep 3

echo "🎯 最終確認..."
curl -I https://touconnect.jp/health

echo "✅ 完成版TOU Connect起動完了！"

EOSSH

echo "🌐 外部確認..."
curl https://touconnect.jp/health

echo ""
echo "🎉 TOU Connect 完成版サイト構築完了！"
echo "🌟 URL: https://touconnect.jp"
echo "🤖 AI分析・学友マッチング・美しいUI完備"
