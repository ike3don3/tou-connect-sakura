#!/bin/bash

# 🔄 DNS反映確認スクリプト
# 使用方法: ./check_dns_status.sh

echo "🌐 DNS反映状況チェック - $(date)"
echo "=================================="

# 基本情報
DOMAIN="touconnect.jp"
WWW_DOMAIN="www.touconnect.jp"
EXPECTED_IP="153.127.55.224"

echo "ドメイン: $DOMAIN"
echo "期待IP: $EXPECTED_IP"
echo ""

# DNS確認関数
check_dns() {
    local domain=$1
    local name=$2
    
    echo "--- $name ---"
    echo -n "DNS解決: "
    
    result=$(dig +short $domain A | head -n1)
    
    if [ -z "$result" ]; then
        echo "❌ 未解決"
        return 1
    elif [ "$result" = "$EXPECTED_IP" ]; then
        echo "✅ $result (正常)"
        return 0
    else
        echo "⚠️  $result (異なるIP)"
        return 1
    fi
}

# HTTP確認関数
check_http() {
    local url=$1
    local name=$2
    
    echo -n "$name HTTP: "
    
    if curl -I -s --connect-timeout 5 "$url" > /dev/null 2>&1; then
        echo "✅ 接続成功"
        return 0
    else
        echo "❌ 接続失敗"
        return 1
    fi
}

# DNS状況確認
dns_main=0
dns_www=0

check_dns $DOMAIN "メインドメイン"
dns_main=$?

check_dns $WWW_DOMAIN "WWWドメイン"
dns_www=$?

echo ""

# HTTP確認 (DNS解決できた場合のみ)
if [ $dns_main -eq 0 ]; then
    check_http "http://$DOMAIN/health" "ドメイン"
fi

if [ $dns_www -eq 0 ]; then
    check_http "http://$WWW_DOMAIN/health" "WWWドメイン"
fi

# IP直接アクセス確認
echo ""
check_http "http://$EXPECTED_IP/health" "IP直接"

echo ""
echo "=================================="

# 結果サマリー
if [ $dns_main -eq 0 ] && [ $dns_www -eq 0 ]; then
    echo "🎉 DNS反映完了！次はSSL設定を行ってください"
    echo "   実行コマンド: ssh ike3don3@$EXPECTED_IP 'sudo ./setup_dns_ssl.sh'"
elif [ $dns_main -eq 0 ] || [ $dns_www -eq 0 ]; then
    echo "⏳ 部分的に反映中。もう少しお待ちください"
else
    echo "⏳ DNS反映待ち。通常30分〜2時間かかります"
fi

echo ""
echo "次回確認: 10分後に再実行してください"
echo "コマンド: ./check_dns_status.sh"
