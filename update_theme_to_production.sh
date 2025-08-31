#!/bin/bash

# TOU Connect - Spectrum.Art #013 テーマ本番反映スクリプト
# 作成日: 2025年8月21日

echo "=== TOU Connect カラーテーマ更新 ==="
echo "新テーマ: Spectrum.Art #013"
echo "実行日時: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# VPS情報
VPS_HOST="153.127.55.224"
VPS_USER="ike3don3"
VPS_PATH="/home/ike3don3/touconnect"

echo "=== 更新対象ファイル ==="
echo "1. static/css/modern.css - メインCSSファイル"
echo "2. templates/index.html - HTMLテンプレート"
echo ""

echo "=== 更新内容確認 ==="
echo "ローカルファイルのカラー設定:"
echo "Primary Color: $(grep -o '#[0-9A-F]\{6\}' static/css/modern.css | head -1)"
echo "Accent Color: $(grep 'accent-color' static/css/modern.css | grep -o '#[0-9A-F]\{6\}')"
echo ""

# 接続テスト
echo "=== VPS接続テスト ==="
if timeout 10 ssh -o ConnectTimeout=5 -o BatchMode=yes $VPS_USER@$VPS_HOST "echo 'Connected'" 2>/dev/null; then
    echo "✅ VPS接続成功"
    
    echo ""
    echo "=== ファイルアップロード ==="
    
    # CSSファイルアップロード
    echo "📁 CSSファイルをアップロード中..."
    if scp -o ConnectTimeout=10 static/css/modern.css $VPS_USER@$VPS_HOST:$VPS_PATH/static/css/; then
        echo "✅ modern.css アップロード完了"
    else
        echo "❌ modern.css アップロード失敗"
    fi
    
    # HTMLテンプレートアップロード
    echo "📁 HTMLテンプレートをアップロード中..."
    if scp -o ConnectTimeout=10 templates/index.html $VPS_USER@$VPS_HOST:$VPS_PATH/templates/; then
        echo "✅ index.html アップロード完了"
    else
        echo "❌ index.html アップロード失敗"
    fi
    
    echo ""
    echo "=== サーバー再起動 ==="
    echo "Gunicornプロセスを再起動中..."
    
    ssh $VPS_USER@$VPS_HOST "cd $VPS_PATH && sudo systemctl restart gunicorn" && \
    echo "✅ Gunicorn再起動完了" || echo "❌ Gunicorn再起動失敗"
    
    echo ""
    echo "=== 更新確認 ==="
    echo "本番サイトの色設定を確認中..."
    
    sleep 3
    PRIMARY_COLOR=$(curl -s https://touconnect.jp/static/css/modern.css | grep -o 'primary-color.*#[0-9A-Fa-f]\{6\}' | head -1)
    
    if echo "$PRIMARY_COLOR" | grep -q "000DB3"; then
        echo "✅ 新しいカラーテーマが本番サイトに反映されました！"
        echo "   $PRIMARY_COLOR"
    else
        echo "⚠️  カラーテーマの反映を確認できません"
        echo "   現在の設定: $PRIMARY_COLOR"
    fi
    
else
    echo "❌ VPS接続失敗"
    echo ""
    echo "=== 手動更新手順 ==="
    echo "以下のコマンドを手動で実行してください："
    echo ""
    echo "1. CSSファイルアップロード:"
    echo "   scp static/css/modern.css $VPS_USER@$VPS_HOST:$VPS_PATH/static/css/"
    echo ""
    echo "2. HTMLテンプレートアップロード:"
    echo "   scp templates/index.html $VPS_USER@$VPS_HOST:$VPS_PATH/templates/"
    echo ""
    echo "3. サーバー再起動:"
    echo "   ssh $VPS_USER@$VPS_HOST 'sudo systemctl restart gunicorn'"
    echo ""
    echo "4. 確認:"
    echo "   curl https://touconnect.jp/static/css/modern.css | grep primary-color"
    echo ""
fi

echo ""
echo "=== ローカルテスト ==="
echo "ローカルでの確認URL:"
echo "- メインページ: http://localhost:5000"
echo "- カラーテスト: file://$(pwd)/color_test.html"
echo ""

echo "=== 更新完了 ==="
echo "Spectrum.Art #013 テーマの更新処理を完了しました。"
echo "本番サイト: https://touconnect.jp"
echo ""

# 最終確認用のURLテスト
echo "=== 最終確認 ==="
echo "本番サイトの応答確認:"
if curl -s -I https://touconnect.jp | head -1 | grep -q "200 OK"; then
    echo "✅ サイトは正常に稼働中"
    echo "🌐 https://touconnect.jp で確認してください"
else
    echo "⚠️  サイトの応答を確認できません"
fi

echo ""
echo "🎨 新しいカラーテーマをお楽しみください！"
