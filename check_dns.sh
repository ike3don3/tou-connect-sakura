#!/bin/bash

# DNS設定確認スクリプト
echo "🌐 DNS設定確認中..."
echo "================================"

echo "📍 touconnect.jp の確認:"
dig +short touconnect.jp A

echo "📍 www.touconnect.jp の確認:"  
dig +short www.touconnect.jp A

echo "📍 期待される結果: 153.127.55.224"
echo "================================"

echo "🔍 詳細DNS情報:"
nslookup touconnect.jp

echo "🌐 HTTP接続テスト:"
curl -I --connect-timeout 10 http://touconnect.jp/health 2>/dev/null || echo "まだ接続できません（DNS反映待ち）"
