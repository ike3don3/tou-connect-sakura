#!/bin/bash

# VPS再起動後の接続テストスクリプト
echo "=== VPS再起動後の接続テスト ==="
echo "実行時刻: $(date)"
echo ""

# 管理画面で確認したIPアドレス
NEW_IP="153.127.55.224"
OLD_IP="163.43.46.130"

echo "=== IPアドレステスト ==="
echo "1. 新IP (153.127.55.224) での接続テスト"
if ssh -o ConnectTimeout=10 -o BatchMode=yes ike3don3@$NEW_IP "echo 'Connected successfully'" 2>/dev/null; then
    echo "✅ 新IP で接続成功！"
    NEW_IP_STATUS="OK"
else
    echo "❌ 新IP で接続失敗"
    NEW_IP_STATUS="NG"
fi

echo ""
echo "2. 旧IP (163.43.46.130) での接続テスト"
if ssh -o ConnectTimeout=10 -o BatchMode=yes ike3don3@$OLD_IP "echo 'Connected successfully'" 2>/dev/null; then
    echo "✅ 旧IP で接続成功！"
    OLD_IP_STATUS="OK"
else
    echo "❌ 旧IP で接続失敗"
    OLD_IP_STATUS="NG"
fi

echo ""
echo "=== 結果まとめ ==="
if [ "$NEW_IP_STATUS" = "OK" ]; then
    echo "🎉 新IPアドレスで接続復旧！"
    echo "更新スクリプトのIPアドレスを変更する必要があります"
    echo ""
    echo "次の手順:"
    echo "1. update_theme_to_production.sh のIPアドレスを更新"
    echo "2. 新テーマをデプロイ"
elif [ "$OLD_IP_STATUS" = "OK" ]; then
    echo "🎉 旧IPアドレスで接続復旧！"
    echo "すぐに新テーマをデプロイできます"
    echo ""
    echo "次の手順:"
    echo "1. ./update_theme_to_production.sh を実行"
else
    echo "⚠️  両方のIPアドレスで接続失敗"
    echo "再起動完了まで待機してください（通常5-10分）"
fi

echo ""
echo "=== 手動確認用コマンド ==="
echo "新IP: ssh ike3don3@$NEW_IP"
echo "旧IP: ssh ike3don3@$OLD_IP"
