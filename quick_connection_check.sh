#!/bin/bash

# VPS接続問題 - 簡単チェック&対処法
# 実行: ./quick_connection_check.sh

VPS_HOST="163.43.46.130"
VPS_USER="ike3don3"

echo "🔍 VPS接続問題の簡単診断"
echo "=========================="
echo ""

# 1. 基本的な接続確認
echo "1️⃣  VPSサーバーの稼働確認..."
if curl -s -I https://touconnect.jp | head -1 | grep -q "200 OK"; then
    echo "   ✅ Webサイトは正常稼働中"
    echo "   → VPSサーバー自体は問題なし"
else
    echo "   ❌ Webサイトにアクセスできません"
    echo "   → VPS全体に問題がある可能性"
fi

echo ""

# 2. ネットワーク接続確認
echo "2️⃣  ネットワーク接続確認..."
if ping -c 3 $VPS_HOST >/dev/null 2>&1; then
    echo "   ✅ VPSにpingが通ります"
    echo "   → ネットワーク接続は正常"
else
    echo "   ❌ VPSにpingが通りません"
    echo "   → ネットワーク問題の可能性"
fi

echo ""

# 3. SSH接続テスト
echo "3️⃣  SSH接続テスト..."
if timeout 10 ssh -o ConnectTimeout=5 -o BatchMode=yes $VPS_USER@$VPS_HOST "echo 'SSH OK'" 2>/dev/null; then
    echo "   ✅ SSH接続成功！"
    echo "   → 問題が解決しています"
    echo ""
    echo "🎨 カラーテーマ更新を実行しますか？ (y/n)"
    read -p "回答: " response
    if [[ $response =~ ^[Yy]$ ]]; then
        ./update_theme_to_production.sh
    fi
else
    echo "   ❌ SSH接続失敗"
    echo "   → SSHサービスに問題があります"
fi

echo ""
echo "📋 対処法の提案"
echo "==============="

echo ""
echo "🟡 自動復旧を待つ場合（推奨）:"
echo "   ./monitor_vps_connection.sh"
echo "   → 5分間隔で接続をチェックし、復旧したら自動更新"

echo ""
echo "🔧 手動で確認する場合:"
echo "   1. VPS管理画面にログイン"
echo "   2. VPSを再起動"
echo "   3. 10-15分後に再試行"

echo ""
echo "⏰ 時間を置いて再試行:"
echo "   ./update_theme_to_production.sh"
echo "   → 30分〜1時間後に実行"

echo ""
echo "📁 緊急時のファイル確認:"
echo "   ローカルファイルは準備完了:"
echo "   - static/css/modern.css (新配色)"
echo "   - templates/index.html (更新済み)"

echo ""
echo "🌐 現在のサイト確認:"
echo "   https://touconnect.jp (旧配色で稼働中)"
echo "   http://localhost:5000 (新配色で確認可能)"

echo ""
echo "💡 結論: 基本的には時間を置いて自動復旧を待つのが最適です"
