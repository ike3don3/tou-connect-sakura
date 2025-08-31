#!/bin/bash
# TOU Connect 本番環境自動デプロイスクリプト

set -e

# 設定
DOMAIN="your-domain.com"
APP_DIR="/opt/tou_connect"
BACKUP_DIR="/opt/backups/tou_connect"
LOG_FILE="/var/log/tou_connect_deploy.log"

# 色付きログ
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌${NC} $1" | tee -a "$LOG_FILE"
}

# 使用方法
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --domain DOMAIN     ドメイン名 (default: $DOMAIN)"
    echo "  --skip-backup       バックアップをスキップ"
    echo "  --skip-ssl          SSL設定をスキップ"
    echo "  --dry-run           実際の変更を行わずにテスト"
    echo "  -h, --help          このヘルプを表示"
    exit 1
}

# 引数解析
SKIP_BACKUP=false
SKIP_SSL=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --skip-ssl)
            SKIP_SSL=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

echo "🚀 TOU Connect 本番環境デプロイ開始"
echo "=================================="
log "Domain: $DOMAIN"
log "App Directory: $APP_DIR"
log "Dry Run: $DRY_RUN"

# 前提条件チェック
check_prerequisites() {
    log "前提条件をチェック中..."
    
    # root権限チェック
    if [[ $EUID -ne 0 ]]; then
        log_error "このスクリプトはroot権限で実行してください"
        exit 1
    fi
    
    # 必要なコマンドの確認
    local commands=("python3" "pip3" "nginx" "systemctl" "psql")
    for cmd in "${commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "必要なコマンドが見つかりません: $cmd"
            exit 1
        fi
    done
    
    # PostgreSQL接続確認
    if ! systemctl is-active --quiet postgresql; then
        log_error "PostgreSQLが起動していません"
        exit 1
    fi
    
    # Redis接続確認
    if ! systemctl is-active --quiet redis-server; then
        log_error "Redisが起動していません"
        exit 1
    fi
    
    log_success "前提条件チェック完了"
}

# バックアップ作成
create_backup() {
    if [[ "$SKIP_BACKUP" == "true" ]]; then
        log_warning "バックアップをスキップしました"
        return
    fi
    
    log "バックアップを作成中..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_name="tou_connect_backup_${timestamp}"
    
    mkdir -p "$BACKUP_DIR"
    
    # データベースバックアップ
    if [[ "$DRY_RUN" == "false" ]]; then
        sudo -u postgres pg_dump tou_connect_prod > "$BACKUP_DIR/${backup_name}.sql"
        log_success "データベースバックアップ完了: ${backup_name}.sql"
        
        # アプリケーションファイルバックアップ
        tar -czf "$BACKUP_DIR/${backup_name}.tar.gz" -C "$APP_DIR" .
        log_success "アプリケーションバックアップ完了: ${backup_name}.tar.gz"
    else
        log "DRY RUN: バックアップをスキップ"
    fi
}

# システムパッケージ更新
update_system() {
    log "システムパッケージを更新中..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        apt update
        apt upgrade -y
        log_success "システム更新完了"
    else
        log "DRY RUN: システム更新をスキップ"
    fi
}

# アプリケーション更新
update_application() {
    log "アプリケーションを更新中..."
    
    cd "$APP_DIR"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # 仮想環境の有効化
        source venv/bin/activate
        
        # 依存関係更新
        pip install --upgrade pip
        pip install -r requirements-production.txt
        
        # データベースマイグレーション（必要に応じて）
        python3 init_database.py
        
        # 静的ファイル最適化
        python3 -c "
try:
    from optimization.static_optimizer import StaticOptimizer
    optimizer = StaticOptimizer()
    optimizer.optimize_directory('static')
    print('静的ファイル最適化完了')
except Exception as e:
    print(f'最適化エラー: {e}')
"
        
        # 権限設定
        chown -R www-data:www-data "$APP_DIR"
        
        log_success "アプリケーション更新完了"
    else
        log "DRY RUN: アプリケーション更新をスキップ"
    fi
}

# Nginx設定更新
update_nginx() {
    log "Nginx設定を更新中..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # ドメイン名を実際の値に置換
        sed "s/your-domain.com/$DOMAIN/g" deployment/nginx_production.conf > /etc/nginx/sites-available/tou_connect
        
        # サイト有効化
        ln -sf /etc/nginx/sites-available/tou_connect /etc/nginx/sites-enabled/
        
        # デフォルトサイト無効化
        rm -f /etc/nginx/sites-enabled/default
        
        # 設定テスト
        nginx -t
        
        log_success "Nginx設定更新完了"
    else
        log "DRY RUN: Nginx設定更新をスキップ"
    fi
}

# SSL証明書設定
setup_ssl() {
    if [[ "$SKIP_SSL" == "true" ]]; then
        log_warning "SSL設定をスキップしました"
        return
    fi
    
    log "SSL証明書を設定中..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Certbot インストール確認
        if ! command -v certbot &> /dev/null; then
            apt install -y certbot python3-certbot-nginx
        fi
        
        # SSL証明書取得
        certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN"
        
        # 自動更新設定
        (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
        
        log_success "SSL証明書設定完了"
    else
        log "DRY RUN: SSL設定をスキップ"
    fi
}

# サービス設定
setup_services() {
    log "サービスを設定中..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Systemd サービスファイル
        cp deployment/tou_connect.service /etc/systemd/system/
        
        # サービス有効化
        systemctl daemon-reload
        systemctl enable tou_connect
        
        log_success "サービス設定完了"
    else
        log "DRY RUN: サービス設定をスキップ"
    fi
}

# サービス再起動
restart_services() {
    log "サービスを再起動中..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # アプリケーション再起動
        systemctl restart tou_connect
        
        # Nginx再起動
        systemctl restart nginx
        
        # サービス状態確認
        sleep 5
        
        if systemctl is-active --quiet tou_connect; then
            log_success "TOU Connect サービス起動完了"
        else
            log_error "TOU Connect サービス起動失敗"
            exit 1
        fi
        
        if systemctl is-active --quiet nginx; then
            log_success "Nginx サービス起動完了"
        else
            log_error "Nginx サービス起動失敗"
            exit 1
        fi
    else
        log "DRY RUN: サービス再起動をスキップ"
    fi
}

# ヘルスチェック
health_check() {
    log "ヘルスチェックを実行中..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "https://$DOMAIN/health" > /dev/null; then
            log_success "ヘルスチェック成功"
            return 0
        fi
        
        log "ヘルスチェック試行 $attempt/$max_attempts..."
        sleep 10
        ((attempt++))
    done
    
    log_error "ヘルスチェック失敗"
    return 1
}

# クリーンアップ
cleanup() {
    log "クリーンアップを実行中..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # 古いバックアップ削除（30日以上）
        find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete 2>/dev/null || true
        find "$BACKUP_DIR" -name "*.sql" -mtime +30 -delete 2>/dev/null || true
        
        # システムクリーンアップ
        apt autoremove -y
        apt autoclean
        
        log_success "クリーンアップ完了"
    else
        log "DRY RUN: クリーンアップをスキップ"
    fi
}

# メイン処理
main() {
    # ログディレクトリ作成
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log "=== デプロイ開始 ==="
    
    check_prerequisites
    create_backup
    update_system
    update_application
    update_nginx
    setup_ssl
    setup_services
    restart_services
    
    if health_check; then
        cleanup
        log_success "=== デプロイ完了 ==="
        echo ""
        echo "🎉 デプロイが正常に完了しました！"
        echo "🌐 アプリケーションURL: https://$DOMAIN"
        echo "📊 監視ダッシュボード: https://$DOMAIN/monitoring"
        echo "📋 ヘルスチェック: https://$DOMAIN/health"
    else
        log_error "=== デプロイ失敗 ==="
        echo ""
        echo "❌ デプロイに失敗しました"
        echo "📋 ログを確認してください: $LOG_FILE"
        echo "🔄 ロールバックが必要な場合があります"
        exit 1
    fi
}

# スクリプト実行
main "$@"