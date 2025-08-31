#!/bin/bash
# TOU Connect Docker Entrypoint Script

set -e

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1"
}

# 環境変数の確認
check_environment() {
    log "環境変数をチェック中..."
    
    # 必須環境変数のチェック
    required_vars=("FLASK_ENV" "SECRET_KEY" "DATABASE_URL")
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "必須環境変数 $var が設定されていません"
            exit 1
        fi
    done
    
    log_success "環境変数チェック完了"
}

# データベース接続待機
wait_for_database() {
    log "データベース接続を待機中..."
    
    # PostgreSQL接続チェック
    if [[ $DATABASE_URL == postgresql* ]]; then
        # PostgreSQLの場合
        host=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
        port=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        
        log "PostgreSQL接続チェック: $host:$port"
        
        for i in {1..30}; do
            if pg_isready -h "$host" -p "$port" > /dev/null 2>&1; then
                log_success "PostgreSQL接続確認完了"
                break
            fi
            
            if [ $i -eq 30 ]; then
                log_error "PostgreSQL接続タイムアウト"
                exit 1
            fi
            
            log "PostgreSQL接続待機中... ($i/30)"
            sleep 2
        done
    else
        log_warning "SQLite使用中（本番環境ではPostgreSQLを推奨）"
    fi
}

# Redis接続チェック
wait_for_redis() {
    if [ -n "$REDIS_URL" ]; then
        log "Redis接続をチェック中..."
        
        # Redis接続チェック
        redis_host=$(echo $REDIS_URL | sed -n 's/redis:\/\/\([^:]*\):.*/\1/p')
        redis_port=$(echo $REDIS_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        
        for i in {1..15}; do
            if redis-cli -h "$redis_host" -p "$redis_port" ping > /dev/null 2>&1; then
                log_success "Redis接続確認完了"
                break
            fi
            
            if [ $i -eq 15 ]; then
                log_warning "Redis接続失敗（キャッシュ機能が無効になります）"
                break
            fi
            
            log "Redis接続待機中... ($i/15)"
            sleep 2
        done
    fi
}

# データベース初期化
initialize_database() {
    log "データベース初期化中..."
    
    # マイグレーション実行
    if [ -f "migrations/alembic.ini" ]; then
        log "Alembicマイグレーション実行中..."
        alembic upgrade head
    else
        log "初期データベーススキーマ作成中..."
        python3 init_database.py
    fi
    
    log_success "データベース初期化完了"
}

# 静的ファイル最適化
optimize_static_files() {
    if [ "$OPTIMIZATION_ENABLED" = "True" ]; then
        log "静的ファイル最適化中..."
        
        # 最適化ディレクトリ作成
        mkdir -p static/optimized
        
        # 最適化実行
        python3 -c "
from optimization.static_optimizer import StaticOptimizer
optimizer = StaticOptimizer()
optimizer.optimize_directory('static')
print('静的ファイル最適化完了')
"
        
        log_success "静的ファイル最適化完了"
    fi
}

# ヘルスチェック準備
prepare_health_check() {
    log "ヘルスチェック準備中..."
    
    # ログディレクトリ作成
    mkdir -p logs
    
    # 権限設定
    chmod 755 logs
    
    log_success "ヘルスチェック準備完了"
}

# メイン処理
main() {
    log "=== TOU Connect 起動準備 ==="
    
    # 環境チェック
    check_environment
    
    # 外部サービス接続待機
    wait_for_database
    wait_for_redis
    
    # アプリケーション準備
    initialize_database
    optimize_static_files
    prepare_health_check
    
    log_success "=== 起動準備完了 ==="
    log "アプリケーション起動中..."
    
    # 引数で渡されたコマンドを実行
    exec "$@"
}

# スクリプト実行
main "$@"