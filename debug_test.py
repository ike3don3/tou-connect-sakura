#!/usr/bin/env python3
"""
デバッグ用テストスクリプト
"""
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

def test_simple_app():
    """シンプルなアプリケーションテスト"""
    try:
        # テスト用の環境変数設定
        os.environ['ENVIRONMENT'] = 'testing'
        os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'
        
        from flask import Flask
        
        # 最もシンプルなFlaskアプリ
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        @app.route('/')
        def index():
            return "Hello World"
        
        with app.test_client() as client:
            response = client.get('/')
            print(f"シンプルアプリテスト: {response.status_code}")
            print(f"レスポンス: {response.get_data(as_text=True)}")
        
        return True
    except Exception as e:
        print(f"シンプルアプリテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_security_manager_only():
    """SecurityManagerのみのテスト"""
    try:
        from flask import Flask
        from security.security_manager import SecurityManager
        
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        security_manager = SecurityManager(app)
        
        print("SecurityManager初期化成功")
        return True
    except Exception as e:
        print(f"SecurityManagerテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_only():
    """設定のみのテスト"""
    try:
        from config.production_config import get_config
        
        config = get_config('testing')
        print(f"設定テスト成功: {config.__class__.__name__}")
        print(f"TESTING: {config.TESTING}")
        print(f"SECRET_KEY: {config.SECRET_KEY}")
        
        return True
    except Exception as e:
        print(f"設定テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 デバッグテスト開始")
    print("=" * 40)
    
    print("1. 設定のみのテスト")
    test_config_only()
    print()
    
    print("2. シンプルアプリテスト")
    test_simple_app()
    print()
    
    print("3. SecurityManagerのみのテスト")
    test_security_manager_only()
    print()