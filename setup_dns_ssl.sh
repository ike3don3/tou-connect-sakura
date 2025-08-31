#!/bin/bash

# 🌐 DNS・SSL設定確認・自動化スクリプト

set -e

# カラー設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 設定
DOMAIN="touconnect.jp"
WWW_DOMAIN="www.touconnect.jp"
EMAIL="admin@touconnect.jp"  # Let's Encryptで使用

echo -e "${BLUE}"
echo "============================================"
echo "🌐 DNS・SSL設定確認・自動化"
echo "============================================"
echo -e "${NC}"
echo "ドメイン: $DOMAIN"
echo "WWWドメイン: $WWW_DOMAIN"
echo ""

# DNS確認
print_step "DNS設定確認"

# 現在のパブリックIPアドレス取得
PUBLIC_IP=$(curl -s ifconfig.me || echo "IP取得失敗")
echo "現在のサーバーIP: $PUBLIC_IP"

# DNS解決確認
print_step "DNSレコード確認"

echo "=== $DOMAIN の解決 ==="
dig +short $DOMAIN A || print_warning "$DOMAIN の解決に失敗"

echo "=== $WWW_DOMAIN の解決 ==="
dig +short $WWW_DOMAIN A || print_warning "$WWW_DOMAIN の解決に失敗"

# より詳細なDNS確認
echo "=== 詳細DNS情報 ==="
nslookup $DOMAIN || true
nslookup $WWW_DOMAIN || true

# DNS反映チェック関数
check_dns_propagation() {
    local domain=$1
    local expected_ip=$2
    
    print_step "$domain のDNS反映チェック"
    
    local resolved_ip=$(dig +short $domain A | head -n1)
    
    if [ "$resolved_ip" = "$expected_ip" ]; then
        print_success "$domain → $resolved_ip (正しく反映済み)"
        return 0
    else
        print_warning "$domain → $resolved_ip (期待値: $expected_ip)"
        return 1
    fi
}

# DNS反映待機
print_step "DNS反映状況確認"
if check_dns_propagation $DOMAIN $PUBLIC_IP && check_dns_propagation $WWW_DOMAIN $PUBLIC_IP; then
    print_success "DNS設定は正しく反映されています"
    DNS_READY=true
else
    print_warning "DNS設定がまだ反映されていません"
    print_warning "設定から最大48時間かかる場合があります"
    DNS_READY=false
fi

# HTTPアクセス確認
print_step "HTTP接続確認"
if curl -I -s --connect-timeout 10 http://$DOMAIN/health > /dev/null 2>&1; then
    print_success "HTTP接続成功: http://$DOMAIN"
    HTTP_READY=true
else
    print_warning "HTTP接続失敗: http://$DOMAIN"
    HTTP_READY=false
fi

# SSL証明書設定
if [ "$DNS_READY" = true ] && [ "$HTTP_READY" = true ]; then
    print_step "SSL証明書設定開始"
    
    # Certbot実行
    print_step "Let's Encrypt SSL証明書取得"
    
    if certbot --nginx \
        --non-interactive \
        --agree-tos \
        --email $EMAIL \
        --domains $DOMAIN,$WWW_DOMAIN \
        --redirect; then
        print_success "SSL証明書取得・設定完了"
        
        # 自動更新設定確認
        print_step "SSL証明書自動更新設定確認"
        if crontab -l | grep -q "certbot renew"; then
            print_success "SSL自動更新は既に設定済み"
        else
            # 自動更新設定追加
            (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
            print_success "SSL自動更新設定を追加しました"
        fi
        
        # HTTPS接続確認
        print_step "HTTPS接続確認"
        if curl -I -s --connect-timeout 10 https://$DOMAIN/health > /dev/null 2>&1; then
            print_success "HTTPS接続成功: https://$DOMAIN"
            HTTPS_READY=true
        else
            print_warning "HTTPS接続失敗: https://$DOMAIN"
            HTTPS_READY=false
        fi
        
    else
        print_error "SSL証明書取得に失敗しました"
        print_warning "DNS設定を確認して、しばらく待ってから再実行してください"
        HTTPS_READY=false
    fi
else
    print_warning "DNS/HTTP設定が完了していないため、SSL設定をスキップします"
    HTTPS_READY=false
fi

# セキュリティヘッダー設定
if [ "$HTTPS_READY" = true ]; then
    print_step "セキュリティヘッダー設定"
    
    # Nginx設定にセキュリティヘッダーを追加
    cat > /tmp/security_headers.conf << 'EOF'
    # セキュリティヘッダー
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' https:;" always;
EOF
    
    # Nginx設定に追加（既存設定がない場合のみ）
    if ! grep -q "X-Frame-Options" /etc/nginx/sites-available/touconnect; then
        # セキュリティヘッダーをlocationブロックに追加
        sed -i '/location \/ {/r /tmp/security_headers.conf' /etc/nginx/sites-available/touconnect
        nginx -t && systemctl reload nginx
        print_success "セキュリティヘッダー設定完了"
    else
        print_success "セキュリティヘッダーは既に設定済み"
    fi
    
    rm -f /tmp/security_headers.conf
fi

# 最終確認とレポート
echo ""
echo -e "${BLUE}"
echo "============================================"
echo "📊 設定完了レポート"
echo "============================================"
echo -e "${NC}"

echo "🌐 ドメイン設定:"
if [ "$DNS_READY" = true ]; then
    echo "  ✅ DNS設定: 正常"
else
    echo "  ⚠️  DNS設定: 反映待ち"
fi

echo "🔗 HTTP接続:"
if [ "$HTTP_READY" = true ]; then
    echo "  ✅ HTTP接続: 正常"
else
    echo "  ❌ HTTP接続: 失敗"
fi

echo "🔒 HTTPS/SSL:"
if [ "$HTTPS_READY" = true ]; then
    echo "  ✅ HTTPS接続: 正常"
    echo "  ✅ SSL証明書: 取得済み"
    echo "  ✅ 自動更新: 設定済み"
else
    echo "  ⚠️  HTTPS: 未設定"
fi

echo ""
echo "🌟 アクセスURL:"
if [ "$HTTPS_READY" = true ]; then
    echo "  🚀 本番サイト: https://$DOMAIN"
    echo "  🚀 WWW版: https://$WWW_DOMAIN"
else
    echo "  🔧 HTTP版: http://$DOMAIN (SSL設定後にHTTPSに移行)"
fi

echo ""
if [ "$DNS_READY" = true ] && [ "$HTTP_READY" = true ] && [ "$HTTPS_READY" = true ]; then
    print_success "🎉 すべての設定が完了しました！サイトは一般公開準備完了です！"
else
    print_warning "⏳ まだ設定が完了していない項目があります"
    echo ""
    echo "次のアクション:"
    if [ "$DNS_READY" = false ]; then
        echo "1. お名前.comでDNS設定確認（Aレコード: @ → $PUBLIC_IP, www → $PUBLIC_IP）"
        echo "2. DNS反映まで最大48時間待機"
    fi
    if [ "$HTTP_READY" = false ]; then
        echo "3. Nginx/アプリケーション設定確認"
    fi
    if [ "$HTTPS_READY" = false ] && [ "$DNS_READY" = true ] && [ "$HTTP_READY" = true ]; then
        echo "4. このスクリプトを再実行してSSL設定"
    fi
fi

exit 0
