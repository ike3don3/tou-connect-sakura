#!/bin/bash

# 🔧 さくらVPS初期設定スクリプト
# VPS側で実行（rootユーザー）

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

echo -e "${BLUE}"
echo "============================================"
echo "🔧 さくらVPS初期設定開始"
echo "============================================"
echo -e "${NC}"

# 前提条件チェック
if [ "$(id -u)" != "0" ]; then
   print_warning "このスクリプトはrootユーザーで実行してください"
   exit 1
fi

# システム更新
print_step "システム更新"
apt update && apt upgrade -y
print_success "システム更新完了"

# 必要なソフトウェアインストール
print_step "必要なソフトウェアインストール"
apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    nginx \
    git \
    ufw \
    htop \
    curl \
    wget \
    unzip \
    certbot \
    python3-certbot-nginx \
    fail2ban
print_success "ソフトウェアインストール完了"

# 作業用ユーザー作成
print_step "作業用ユーザー作成"
if ! id "touconnect" &>/dev/null; then
    adduser --disabled-password --gecos "" touconnect
    usermod -aG sudo touconnect
    print_success "ユーザー 'touconnect' を作成しました"
else
    print_warning "ユーザー 'touconnect' は既に存在します"
fi

# SSH設定
print_step "SSH設定"
mkdir -p /home/touconnect/.ssh
if [ -f /root/.ssh/authorized_keys ]; then
    cp /root/.ssh/authorized_keys /home/touconnect/.ssh/
    chown -R touconnect:touconnect /home/touconnect/.ssh
    chmod 700 /home/touconnect/.ssh
    chmod 600 /home/touconnect/.ssh/authorized_keys
    print_success "SSH鍵をコピーしました"
fi

# SSH設定強化
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
systemctl restart ssh
print_success "SSH設定強化完了"

# ファイアウォール設定
print_step "ファイアウォール設定"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable
print_success "ファイアウォール設定完了"

# Fail2ban設定
print_step "Fail2ban設定"
systemctl enable fail2ban
systemctl start fail2ban
print_success "Fail2ban設定完了"

# Nginx初期設定
print_step "Nginx初期設定"
systemctl enable nginx
systemctl start nginx

# デフォルトサイト無効化
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

systemctl reload nginx
print_success "Nginx初期設定完了"

# ディレクトリ作成
print_step "アプリケーション用ディレクトリ作成"
sudo -u touconnect mkdir -p /home/touconnect/apps
sudo -u touconnect mkdir -p /home/touconnect/logs
print_success "ディレクトリ作成完了"

# システム設定最適化
print_step "システム設定最適化"

# スワップファイル作成（メモリが少ない場合）
if [ ! -f /swapfile ]; then
    fallocate -l 1G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    print_success "スワップファイル作成完了"
fi

# タイムゾーン設定
timedatectl set-timezone Asia/Tokyo
print_success "タイムゾーン設定完了"

# ログローテーション設定
cat > /etc/logrotate.d/touconnect << 'EOF'
/home/touconnect/apps/tou_connect/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su touconnect touconnect
}
EOF
print_success "ログローテーション設定完了"

# 自動更新設定
print_step "自動セキュリティ更新設定"
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
print_success "自動更新設定完了"

# 完了メッセージ
echo ""
echo -e "${GREEN}"
echo "============================================"
echo "🎉 さくらVPS初期設定完了！"
echo "============================================"
echo -e "${NC}"
echo "✅ システム更新完了"
echo "✅ 必要ソフトウェアインストール完了"
echo "✅ ユーザー 'touconnect' 作成完了"
echo "✅ SSH設定強化完了"
echo "✅ ファイアウォール設定完了"
echo "✅ Nginx設定完了"
echo "✅ セキュリティ強化完了"
echo ""
print_success "次のステップ:"
echo "1. 'touconnect' ユーザーでログインして動作確認"
echo "2. アプリケーションデプロイ"
echo "3. DNS設定"
echo "4. SSL証明書設定"
echo ""
print_warning "重要: 今後は 'touconnect' ユーザーを使用してください"
print_warning "root ログインは無効化されました"

exit 0
