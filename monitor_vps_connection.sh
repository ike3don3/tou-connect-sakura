#!/bin/bash

# VPS接続復旧確認スクリプト
# 定期的にSSH接続をテストして復旧を自動検知

VPS_HOST="163.43.46.130"
VPS_USER="ike3don3"
CHECK_INTERVAL=300  # 5分間隔

echo "=== VPS接続復旧監視開始 ==="
echo "対象: $VPS_USER@$VPS_HOST"
echo "チェック間隔: ${CHECK_INTERVAL}秒 ($(($CHECK_INTERVAL / 60))分)"
echo "開始時刻: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "Ctrl+C で監視を停止できます"
echo ""

attempt=1

while true; do
    echo "[$attempt] $(date '+%H:%M:%S') - 接続テスト中..."
    
    if timeout 10 ssh -o ConnectTimeout=5 -o BatchMode=yes $VPS_USER@$VPS_HOST "echo 'Connection restored'" 2>/dev/null; then
        echo ""
        echo "🎉 VPS接続が復旧しました！"
        echo "復旧時刻: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        
        # 自動でテーマ更新スクリプトを実行するかユーザーに確認
        echo "カラーテーマの更新を自動で実行しますか？ (y/n)"
        read -t 30 -p "30秒以内に応答してください: " response
        
        if [[ $response =~ ^[Yy]$ ]]; then
            echo ""
            echo "🎨 Spectrum.Art #013 テーマ更新を開始します..."
            ./update_theme_to_production.sh
            break
        else
            echo ""
            echo "手動で以下のコマンドを実行してください:"
            echo "./update_theme_to_production.sh"
            break
        fi
    else
        echo "   ❌ まだ接続できません"
    fi
    
    attempt=$((attempt + 1))
    sleep $CHECK_INTERVAL
done

echo ""
echo "=== 監視終了 ==="
