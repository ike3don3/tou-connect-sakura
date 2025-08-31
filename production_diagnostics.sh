#!/bin/bash

# 🔍 TOU Connect 本番環境 診断ツール
# VPSにアクセスせずに外部から診断

echo "🔍 TOU Connect 本番環境診断開始..."
echo "=================================="

# カラー設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DOMAIN="touconnect.jp"
IP="153.127.55.224"

print_test() {
    echo -e "${BLUE}🧪 $1${NC}"
}

print_ok() {
    echo -e "${GREEN}  ✅ $1${NC}"
}

print_warn() {
    echo -e "${YELLOW}  ⚠️  $1${NC}"
}

print_fail() {
    echo -e "${RED}  ❌ $1${NC}"
}

# 1. DNS解決テスト
print_test "DNS解決テスト"
if dig +short $DOMAIN A | grep -q "$IP"; then
    print_ok "DNS正常: $DOMAIN → $IP"
else
    print_fail "DNS異常: $DOMAIN が $IP に解決されません"
fi

# 2. サーバー接続テスト
print_test "サーバー接続テスト"
if ping -c 2 $IP > /dev/null 2>&1; then
    print_ok "サーバー接続: $IP 応答あり"
else
    print_fail "サーバー接続: $IP 応答なし"
fi

# 3. ポート開放テスト
print_test "ポート開放テスト"
if nc -z -w5 $IP 80 2>/dev/null; then
    print_ok "ポート80: 開放"
else
    print_fail "ポート80: 閉鎖またはフィルタ"
fi

if nc -z -w5 $IP 443 2>/dev/null; then
    print_ok "ポート443: 開放"
else
    print_fail "ポート443: 閉鎖またはフィルタ"
fi

# 4. HTTP接続テスト
print_test "HTTP接続テスト"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/ 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "301" ] || [ "$HTTP_STATUS" = "302" ]; then
    print_ok "HTTP: リダイレクト ($HTTP_STATUS) - 正常"
elif [ "$HTTP_STATUS" = "200" ]; then
    print_ok "HTTP: 直接アクセス可能 ($HTTP_STATUS)"
else
    print_fail "HTTP: 異常 (Status: $HTTP_STATUS)"
fi

# 5. HTTPS接続テスト
print_test "HTTPS接続テスト"
HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/ 2>/dev/null || echo "000")
if [ "$HTTPS_STATUS" = "200" ]; then
    print_ok "HTTPS: 正常接続 ($HTTPS_STATUS)"
elif [ "$HTTPS_STATUS" = "000" ]; then
    print_fail "HTTPS: SSL証明書またはサーバー問題"
else
    print_warn "HTTPS: 異常 (Status: $HTTPS_STATUS)"
fi

# 6. SSL証明書テスト
print_test "SSL証明書テスト"
if openssl s_client -connect $DOMAIN:443 -servername $DOMAIN < /dev/null 2>/dev/null | grep -q "Verify return code: 0"; then
    print_ok "SSL証明書: 有効"
else
    print_fail "SSL証明書: 無効または期限切れ"
fi

# 7. ヘルスチェックAPI
print_test "ヘルスチェックAPI"
HEALTH_RESPONSE=$(curl -s https://$DOMAIN/health 2>/dev/null || echo "")
if echo "$HEALTH_RESPONSE" | grep -q "healthy\|operational\|status"; then
    print_ok "ヘルスチェック: 正常応答"
    echo "    レスポンス: $HEALTH_RESPONSE"
else
    print_fail "ヘルスチェック: 異常応答またはアクセス不可"
fi

# 8. Webサーバー情報
print_test "Webサーバー情報"
SERVER_INFO=$(curl -s -I http://$DOMAIN/ 2>/dev/null | grep -i server || echo "不明")
echo "    $SERVER_INFO"

echo ""
echo "🎯 診断結果サマリー"
echo "=================="

# 簡易スコア計算
SCORE=0
[ "$(dig +short $DOMAIN A)" = "$IP" ] && SCORE=$((SCORE + 1))
[ "$(ping -c 1 $IP > /dev/null 2>&1; echo $?)" = "0" ] && SCORE=$((SCORE + 1))
[ "$(nc -z -w5 $IP 443 2>/dev/null; echo $?)" = "0" ] && SCORE=$((SCORE + 1))
[ "$HTTPS_STATUS" = "200" ] && SCORE=$((SCORE + 2))
[ "$HEALTH_RESPONSE" != "" ] && echo "$HEALTH_RESPONSE" | grep -q "healthy\|operational" && SCORE=$((SCORE + 2))

echo "診断スコア: $SCORE/7"

if [ $SCORE -ge 6 ]; then
    echo -e "${GREEN}🎉 本番環境は正常に動作しています${NC}"
elif [ $SCORE -ge 4 ]; then
    echo -e "${YELLOW}⚠️  本番環境に軽微な問題があります${NC}"
    echo "推奨: SSL証明書またはアプリケーション設定を確認してください"
else
    echo -e "${RED}🚨 本番環境に重大な問題があります${NC}"
    echo "推奨: 手動修正ガイド (PRODUCTION_FIX_MANUAL.md) を実行してください"
fi

echo ""
echo "🔗 アクセスURL:"
echo "   メインサイト: https://$DOMAIN"
echo "   ヘルスチェック: https://$DOMAIN/health"
echo ""
