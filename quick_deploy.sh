#!/bin/bash
# TOU Connect 簡単デプロイスクリプト

set -e

echo "🚀 TOU Connect 簡単デプロイ"
echo "=========================="

# 色付きログ
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# デプロイタイプの選択
echo "デプロイタイプを選択してください:"
echo "1) ローカル開発環境"
echo "2) ローカル本番環境テスト"
echo "3) VPS/クラウドサーバー"
echo "4) Docker環境"

read -p "選択 (1-4): " deploy_type

case $deploy_type in
    1)
        log_info "ローカル開発環境デプロイを開始します"
        
        # 開発環境設定
        export FLASK_ENV=development
        export FLASK_DEBUG=True
        
        # 仮想環境作成
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi
        
        source venv/bin/activate
        pip install -r requirements.txt
        
        # データベース初期化
        python3 init_database.py
        
        log_success "開発環境準備完了"
        log_info "アプリケーションを起動します..."
        
        python3 app.py
        ;;
        
    2)
        log_info "ローカル本番環境テストを開始します"
        ./deploy_local.sh
        ;;
        
    3)
        log_info "VPS/クラウドサーバーデプロイガイドを表示します"
        
        echo ""
        echo "📋 VPS/クラウドサーバーデプロイ手順:"
        echo ""
        echo "1. サーバーにファイルをアップロード:"
        echo "   scp -r tou_connect/ user@your-server:/opt/"
        echo ""
        echo "2. サーバーにログインして以下を実行:"
        echo "   cd /opt/tou_connect"
        echo "   ./scripts/deploy.sh --env production"
        echo ""
        echo "3. 詳細な手順は PRODUCTION_DEPLOYMENT_GUIDE.md を参照"
        echo ""
        
        read -p "デプロイガイドを開きますか？ (y/N): " open_guide
        if [[ "$open_guide" =~ ^[Yy]$ ]]; then
            if command -v code &> /dev/null; then
                code PRODUCTION_DEPLOYMENT_GUIDE.md
            elif command -v nano &> /dev/null; then
                nano PRODUCTION_DEPLOYMENT_GUIDE.md
            else
                cat PRODUCTION_DEPLOYMENT_GUIDE.md
            fi
        fi
        ;;
        
    4)
        log_info "Docker環境デプロイを開始します"
        
        if ! command -v docker &> /dev/null; then
            log_error "Dockerがインストールされていません"
            log_info "Dockerをインストールしてから再実行してください"
            exit 1
        fi
        
        # Docker Compose確認
        if command -v docker-compose &> /dev/null; then
            COMPOSE_CMD="docker-compose"
        elif docker compose version &> /dev/null; then
            COMPOSE_CMD="docker compose"
        else
            log_error "Docker Composeが見つかりません"
            exit 1
        fi
        
        log_info "Docker環境を構築中..."
        
        # 開発環境用Docker Compose実行
        $COMPOSE_CMD -f docker-compose.dev.yml up --build -d
        
        log_success "Docker環境起動完了"
        log_info "アプリケーションURL: http://localhost:5000"
        log_info "停止コマンド: $COMPOSE_CMD -f docker-compose.dev.yml down"
        ;;
        
    *)
        log_error "無効な選択です"
        exit 1
        ;;
esac

echo ""
echo "=========================="
log_success "デプロイ完了！"

# 次のステップの案内
echo ""
echo "🎯 次のステップ:"
case $deploy_type in
    1)
        echo "- ブラウザで http://localhost:5000 にアクセス"
        echo "- 開発を開始してください！"
        ;;
    2)
        echo "- 本番環境設定を確認・修正"
        echo "- 実際のサーバーへのデプロイを検討"
        ;;
    3)
        echo "- サーバーの準備（PostgreSQL、Redis等）"
        echo "- ドメイン・SSL証明書の設定"
        echo "- 実際のデプロイ実行"
        ;;
    4)
        echo "- ブラウザで http://localhost:5000 にアクセス"
        echo "- 本番環境用設定の調整"
        ;;
esac

echo ""
echo "📚 参考資料:"
echo "- PRODUCTION_DEPLOYMENT_GUIDE.md: 詳細なデプロイ手順"
echo "- PRODUCTION_CHECKLIST.md: 本番環境チェックリスト"
echo "- README.md: アプリケーション概要"