#!/bin/bash

# 定期的な復旧チェックスクリプト
echo "=== 復旧状況定期チェック ==="
echo "開始時刻: $(date)"
echo ""

for i in {1..10}; do
    echo "[$i/10] チェック中... $(date '+%H:%M:%S')"
    
    # Webサイト応答確認
    if curl -s -I https://touconnect.jp 2>/dev/null | grep -q "200 OK"; then
        echo "✅ Webサイト復旧！"
        SITE_OK=true
    else
        echo "❌ Webサイト未復旧"
        SITE_OK=false
    fi
    
    # SSH接続確認（旧IP）
    if ssh -o ConnectTimeout=5 -o BatchMode=yes ike3don3@163.43.46.130 "echo 'test'" 2>/dev/null; then
        echo "✅ SSH接続復旧（旧IP）！"
        SSH_OLD_OK=true
    else
        echo "❌ SSH接続未復旧（旧IP）"
        SSH_OLD_OK=false
    fi
    
    # SSH接続確認（新IP）
    if ssh -o ConnectTimeout=5 -o BatchMode=yes ike3don3@153.127.55.224 "echo 'test'" 2>/dev/null; then
        echo "✅ SSH接続復旧（新IP）！"
        SSH_NEW_OK=true
    else
        echo "❌ SSH接続未復旧（新IP）"
        SSH_NEW_OK=false
    fi
    
    echo ""
    
    # 復旧チェック
    if [ "$SITE_OK" = true ] && ([ "$SSH_OLD_OK" = true ] || [ "$SSH_NEW_OK" = true ]); then
        echo "🎉 完全復旧しました！"
        echo ""
        echo "=== 自動テーマ更新を開始 ==="
        if [ "$SSH_OLD_OK" = true ]; then
            echo "旧IPアドレスで接続 - 既存スクリプト使用"
            ./update_theme_to_production.sh
        else
            echo "新IPアドレスで接続 - スクリプト更新後実行"
            # IPアドレス更新が必要
        fi
        break
    fi
    
    if [ $i -lt 10 ]; then
        echo "30秒待機..."
        sleep 30
    fi
done

echo ""
echo "=== 最終状況 ==="
echo "Webサイト: $([ "$SITE_OK" = true ] && echo "✅ 正常" || echo "❌ 異常")"
echo "SSH(旧IP): $([ "$SSH_OLD_OK" = true ] && echo "✅ 接続可" || echo "❌ 接続不可")"
echo "SSH(新IP): $([ "$SSH_NEW_OK" = true ] && echo "✅ 接続可" || echo "❌ 接続不可")"
echo ""
echo "完了時刻: $(date)"
