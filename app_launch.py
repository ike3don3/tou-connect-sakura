#!/usr/bin/env python3
"""
TOU Connect Application Launcher
本番環境用のアプリケーション起動ファイル
"""
import os
import sys
import logging
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 環境設定の読み込み
from dotenv import load_dotenv

# 環境に応じた設定ファイルの読み込み
env = os.getenv('FLASK_ENV', 'production')
if env == 'production':
    load_dotenv('.env.production')
else:
    load_dotenv('.env')

# アプリケーションのインポート
from app import app
from config.production_config import ProductionConfig
from security.security_manager import SecurityManager
from monitoring.monitoring_manager import MonitoringManager
from infrastructure.logging_manager import LoggingManager


def setup_production_environment():
    """本番環境のセットアップ"""
    try:
        # 本番環境設定の適用
        if os.getenv('FLASK_ENV') == 'production':
            app.config.from_object(ProductionConfig)
            
            # セキュリティマネージャーの初期化
            security_manager = SecurityManager()
            security_manager.setup_security_headers(app)
            
            # 監視システムの初期化
            monitoring_manager = MonitoringManager()
            monitoring_manager.setup_monitoring(app)
            
            # ログシステムの初期化
            logging_manager = LoggingManager()
            logging_manager.setup_production_logging()
            
            print(f"✅ 本番環境設定完了 - {datetime.now()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 本番環境設定エラー: {e}")
        return False


def validate_environment():
    """環境変数の検証"""
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'GEMINI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 必須環境変数が不足: {', '.join(missing_vars)}")
        return False
    
    # 開発用設定の警告
    if os.getenv('SECRET_KEY') == 'dev-secret-key-change-in-production':
        print("⚠️ 警告: 開発用SECRET_KEYが使用されています")
    
    return True


def main():
    """メイン関数"""
    print("🚀 TOU Connect 起動中...")
    
    # 環境変数検証
    if not validate_environment():
        sys.exit(1)
    
    # 本番環境セットアップ
    if not setup_production_environment():
        sys.exit(1)
    
    print("✅ TOU Connect 起動準備完了")
    return app


# WSGIアプリケーションオブジェクト
app = main()

if __name__ == '__main__':
    # 開発環境での直接実行
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') != 'production'
    
    print(f"🌐 開発サーバー起動: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)