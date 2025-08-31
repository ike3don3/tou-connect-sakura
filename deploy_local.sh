#!/bin/bash
# ローカル本番環境デプロイテスト

set -e

echo "🚀 TOU Connect ローカル本番環境デプロイテスト"
echo "=============================================="

# 色付きログ
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. 環境設定
echo "📋 1. 環境設定確認中..."

if [ ! -f ".env.production" ]; then
    log_error ".env.production ファイルが見つかりません"
    exit 1
fi

# 本番環境変数の設定
export FLASK_ENV=production
export FLASK_DEBUG=False

log_success "環境設定完了"

# 2. 依存関係インストール
echo "📦 2. 依存関係インストール中..."

if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    log_error "Pythonが見つかりません"
    exit 1
fi

# 仮想環境の作成（存在しない場合）
if [ ! -d "venv" ]; then
    log_warning "仮想環境を作成中..."
    $PYTHON_CMD -m venv venv
fi

# 仮想環境の有効化
source venv/bin/activate

# 依存関係インストール
pip install --upgrade pip
pip install -r requirements-production.txt

log_success "依存関係インストール完了"

# 3. データベース初期化
echo "🗄️ 3. データベース初期化中..."

$PYTHON_CMD init_database.py

log_success "データベース初期化完了"

# 4. 静的ファイル最適化
echo "⚡ 4. 静的ファイル最適化中..."

mkdir -p static/optimized

$PYTHON_CMD -c "
try:
    from optimization.static_optimizer import StaticOptimizer
    optimizer = StaticOptimizer()
    optimizer.optimize_directory('static')
    print('静的ファイル最適化完了')
except Exception as e:
    print(f'最適化スキップ: {e}')
"

log_success "静的ファイル最適化完了"

# 5. セキュリティチェック
echo "🔒 5. セキュリティチェック中..."

$PYTHON_CMD -c "
import os
from dotenv import load_dotenv
load_dotenv('.env.production')

issues = []
if os.getenv('SECRET_KEY') == 'CHANGE_THIS_IN_PRODUCTION_TO_SECURE_RANDOM_STRING':
    issues.append('SECRET_KEYが変更されていません')
if os.getenv('FLASK_DEBUG', '').lower() == 'true':
    issues.append('デバッグモードが有効です')

if issues:
    print('⚠️ セキュリティ警告:')
    for issue in issues:
        print(f'  - {issue}')
else:
    print('✅ セキュリティチェック完了')
"

# 6. アプリケーション起動テスト
echo "🌐 6. アプリケーション起動テスト中..."

# バックグラウンドでアプリケーション起動
$PYTHON_CMD app_launch.py &
APP_PID=$!

# 起動待機
sleep 5

# ヘルスチェック
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    log_success "アプリケーション起動成功"
    
    # 基本エンドポイントテスト
    echo "🧪 基本機能テスト中..."
    
    if curl -f http://localhost:5000/ > /dev/null 2>&1; then
        log_success "メインページ正常"
    else
        log_warning "メインページアクセス失敗"
    fi
    
    if curl -f http://localhost:5000/api/monitoring/overview > /dev/null 2>&1; then
        log_success "監視API正常"
    else
        log_warning "監視APIアクセス失敗"
    fi
    
else
    log_error "アプリケーション起動失敗"
fi

# アプリケーション停止
kill $APP_PID 2>/dev/null || true

# 7. 本番準備チェック
echo "📊 7. 最終本番準備チェック..."

$PYTHON_CMD production_readiness_check.py

echo ""
echo "=============================================="
echo "🎉 ローカル本番環境デプロイテスト完了"
echo ""
echo "次のステップ:"
echo "1. .env.production の設定値を本番環境用に変更"
echo "2. PostgreSQL データベースの準備"
echo "3. Redis サーバーの準備"
echo "4. SSL証明書の取得"
echo "5. 本番サーバーへのデプロイ"
echo ""
echo "本番デプロイコマンド:"
echo "  ./scripts/deploy.sh --env production"
echo "=============================================="