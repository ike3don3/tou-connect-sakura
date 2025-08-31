#!/bin/bash
# TOU Connect さくらのVPS用デプロイスクリプト

set -e

# さくらのVPS設定
DOMAIN="touconnect.jp"
SERVER_IP="153.127.55.224"
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

echo "🚀 TOU Connect さくらのVPS デプロイ"
echo "===================================="
echo "ドメイン: $DOMAIN"
echo "サーバーIP: $SERVER_IP"
echo "アプリディレクトリ: $APP_DIR"
echo ""

# 引数解析
SKIP_BACKUP=false
SKIP_SSL=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
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
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --skip-backup   バックアップをスキップ"
            echo "  --skip-ssl      SSL設定をスキップ"
            echo "  --dry-run       実際の変更を行わずにテスト"
            echo "  -h, --help      このヘルプを表示"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# root権限チェック
if [[ $EUID -ne 0 ]]; then
    log_error "このスクリプトはroot権限で実行してください"
    exit 1
fi

# さくらのVPS用システム準備
setup_sakura_vps() {
    log "さくらのVPS用システム準備中..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # システム更新
        apt update && apt upgrade -y
        
        # 必要パッケージインストール
        apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server git curl ufw
        
        # ファイアウォール設定（さくらのVPS用）
        ufw --force reset
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow ssh
        ufw allow 'Nginx Full'
        ufw --force enable
        
        log_success "システム準備完了"
    else
        log "DRY RUN: システム準備をスキップ"
    fi
}

# PostgreSQL設定（さくらのVPS用）
setup_postgresql() {
    log "PostgreSQL設定中..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # PostgreSQL設定
        systemctl enable postgresql
        systemctl start postgresql
        
        # データベースとユーザー作成
        sudo -u postgres psql -c "CREATE USER tou_connect WITH PASSWORD 'TouConnect2024!Sakura';" || true
        sudo -u postgres psql -c "CREATE DATABASE tou_connect_prod OWNER tou_connect;" || true
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE tou_connect_prod TO tou_connect;" || true
        
        # PostgreSQL設定調整（さくらのVPS用）
        PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP '\d+\.\d+' | head -1)
        PG_CONFIG="/etc/postgresql/$PG_VERSION/main/postgresql.conf"
        
        if [[ -f "$PG_CONFIG" ]]; then
            # メモリ設定調整（2GB RAM想定）
            sed -i "s/#shared_buffers = 128MB/shared_buffers = 256MB/" "$PG_CONFIG"
            sed -i "s/#effective_cache_size = 4GB/effective_cache_size = 1GB/" "$PG_CONFIG"
            sed -i "s/#maintenance_work_mem = 64MB/maintenance_work_mem = 64MB/" "$PG_CONFIG"
            
            systemctl restart postgresql
        fi
        
        log_success "PostgreSQL設定完了"
    else
        log "DRY RUN: PostgreSQL設定をスキップ"
    fi
}

# Redis設定（さくらのVPS用）
setup_redis() {
    log "Redis設定中..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        systemctl enable redis-server
        systemctl start redis-server
        
        # Redis設定調整
        REDIS_CONFIG="/etc/redis/redis.conf"
        if [[ -f "$REDIS_CONFIG" ]]; then
            # メモリ制限設定（256MB）
            sed -i "s/# maxmemory <bytes>/maxmemory 256mb/" "$REDIS_CONFIG"
            sed -i "s/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/" "$REDIS_CONFIG"
            
            systemctl restart redis-server
        fi
        
        log_success "Redis設定完了"
    else
        log "DRY RUN: Redis設定をスキップ"
    fi
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
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # データベースバックアップ
        if systemctl is-active --quiet postgresql; then
            sudo -u postgres pg_dump tou_connect_prod > "$BACKUP_DIR/${backup_name}.sql" 2>/dev/null || true
            log_success "データベースバックアップ完了: ${backup_name}.sql"
        fi
        
        # アプリケーションファイルバックアップ
        if [[ -d "$APP_DIR" ]]; then
            tar -czf "$BACKUP_DIR/${backup_name}.tar.gz" -C "$APP_DIR" . 2>/dev/null || true
            log_success "アプリケーションバックアップ完了: ${backup_name}.tar.gz"
        fi
    else
        log "DRY RUN: バックアップをスキップ"
    fi
}

# アプリケーション設定
setup_application() {
    log "アプリケーション設定中..."
    
    cd "$APP_DIR"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # 仮想環境作成
        python3 -m venv venv
        source venv/bin/activate
        
        # 依存関係インストール
        pip install --upgrade pip
        pip install -r requirements-production.txt
        
        # 環境設定ファイル作成
        if [[ ! -f ".env" ]]; then
            cp .env.production .env
            
            # さくらのVPS用設定を適用
            sed -i "s/your-secure-password/TouConnect2024!Sakura/" .env
            sed -i "s/postgresql:\/\/tou_connect:CHANGE_PASSWORD@localhost:5432\/tou_connect_prod/postgresql:\/\/tou_connect:TouConnect2024!Sakura@localhost:5432\/tou_connect_prod/" .env
            
            log_warning "環境設定ファイル(.env)を確認・編集してください"
        fi
        
        # データベース初期化
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
" || true
        
        # 権限設定
        chown -R www-data:www-data "$APP_DIR"
        
        log_success "アプリケーション設定完了"
    else
        log "DRY RUN: アプリケーション設定をスキップ"
    fi
}

# Nginx設定（さくらのVPS用）
setup_nginx() {
    log "Nginx設定中..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # さくらのVPS用Nginx設定を使用
        cp deployment/nginx_sakura.conf /etc/nginx/sites-available/tou_connect
        
        # サイト有効化
        ln -sf /etc/nginx/sites-available/tou_connect /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/default
        
        # 設定テスト
        nginx -t
        
        log_success "Nginx設定完了"
    else
        log "DRY RUN: Nginx設定をスキップ"
    fi
}

# SSL証明書設定（Let's Encrypt）
setup_ssl() {
    if [[ "$SKIP_SSL" == "true" ]]; then
        log_warning "SSL設定をスキップしました"
        return
    fi
    
    log "SSL証明書設定中..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Certbot インストール
        apt install -y certbot python3-certbot-nginx
        
        # SSL証明書取得
        certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN" || {
            log_warning "SSL証明書の自動取得に失敗しました。手動で設定してください。"
            log_warning "コマンド: certbot --nginx -d $DOMAIN -d www.$DOMAIN"
        }
        
        # 自動更新設定
        (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
        
        log_success "SSL証明書設定完了"
    else
        log "DRY RUN: SSL設定をスキップ"
    fi
}

# サービス設定
setup_services() {
    log "サービス設定中..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Systemd サービスファイル
        cp deployment/tou_connect.service /etc/systemd/system/
        
        # サービス有効化・起動
        systemctl daemon-reload
        systemctl enable tou_connect
        systemctl start tou_connect
        
        # Nginx再起動
        systemctl restart nginx
        
        log_success "サービス設定完了"
    else
        log "DRY RUN: サービス設定をスキップ"
    fi
}

# ヘルスチェック
health_check() {
    log "ヘルスチェック実行中..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "http://localhost:8000/health" > /dev/null; then
            log_success "ローカルヘルスチェック成功"
            
            # HTTPS確認（SSL設定済みの場合）
            if [[ "$SKIP_SSL" == "false" ]] && curl -f -s "https://$DOMAIN/health" > /dev/null; then
                log_success "HTTPS ヘルスチェック成功"
            fi
            
            return 0
        fi
        
        log "ヘルスチェック試行 $attempt/$max_attempts..."
        sleep 10
        ((attempt++))
    done
    
    log_error "ヘルスチェック失敗"
    return 1
}

# メイン処理
main() {
    # ログディレクトリ作成
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log "=== さくらのVPS デプロイ開始 ==="
    
    setup_sakura_vps
    setup_postgresql
    setup_redis
    create_backup
    setup_application
    setup_nginx
    setup_ssl
    setup_services
    
    if health_check; then
        log_success "=== デプロイ完了 ==="
        echo ""
        echo "🎉 TOU Connect デプロイが正常に完了しました！"
        echo ""
        echo "📋 アクセス情報:"
        echo "🌐 メインサイト: https://$DOMAIN"
        echo "📊 ヘルスチェック: https://$DOMAIN/health"
        echo "🔧 監視ダッシュボード: https://$DOMAIN/monitoring"
        echo ""
        echo "📝 次のステップ:"
        echo "1. .env ファイルの API キーを設定"
        echo "2. DNS 設定の確認"
        echo "3. 基本機能テストの実行"
        echo "4. 監視・アラート設定"
        echo ""
        echo "📞 サポート:"
        echo "ログファイル: $LOG_FILE"
        echo "サービス状態: systemctl status tou_connect"
    else
        log_error "=== デプロイ失敗 ==="
        echo ""
        echo "❌ デプロイに失敗しました"
        echo "📋 ログを確認してください: $LOG_FILE"
        echo "🔧 トラブルシューティング: journalctl -u tou_connect -f"
        exit 1
    fi
}

# スクリプト実行
main "$@"