#!/usr/bin/env python3
"""
TOU Connect 本番環境起動スクリプト
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# 本番環境設定を読み込み
load_dotenv('.env.production')

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/production.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def ensure_directories():
    """必要なディレクトリを作成"""
    directories = ['logs', 'backups', 'static/optimized']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    logger.info("必要なディレクトリを作成しました")

def check_dependencies():
    """依存関係チェック"""
    try:
        import flask
        import gunicorn
        logger.info(f"Flask: {flask.__version__}")
        logger.info(f"Gunicorn: {gunicorn.__version__}")
        return True
    except ImportError as e:
        logger.error(f"依存関係エラー: {e}")
        return False

def initialize_database():
    """データベース初期化"""
    try:
        from app_launch import init_simple_database
        init_simple_database()
        logger.info("データベース初期化完了")
    except Exception as e:
        logger.error(f"データベース初期化エラー: {e}")
        return False
    return True

def start_production_server():
    """本番サーバー開始"""
    ensure_directories()
    
    if not check_dependencies():
        sys.exit(1)
    
    if not initialize_database():
        sys.exit(1)
    
    logger.info("🚀 TOU Connect 本番環境を開始します...")
    
    # Gunicorn設定
    port = os.getenv('PORT', '8000')
    host = os.getenv('HOST', '0.0.0.0')
    workers = '4'
    
    cmd = [
        'gunicorn',
        '--bind', f'{host}:{port}',
        '--workers', workers,
        '--worker-class', 'gevent',
        '--worker-connections', '1000',
        '--timeout', '30',
        '--keepalive', '2',
        '--max-requests', '1000',
        '--max-requests-jitter', '100',
        '--preload',
        '--access-logfile', 'logs/access.log',
        '--error-logfile', 'logs/error.log',
        '--log-level', 'info',
        'app_launch:app'
    ]
    
    logger.info(f"サーバー起動: {' '.join(cmd)}")
    os.execvp('gunicorn', cmd)

if __name__ == '__main__':
    start_production_server()
