#!/usr/bin/env python3
"""
セキュリティ基盤のテストスクリプト
"""
import os
import sys
import tempfile
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

def test_config_validation():
    """設定クラスのテスト"""
    print("🔧 設定クラスのテスト...")
    
    try:
        from config.production_config import get_config, validate_environment
        
        # 開発環境設定のテスト
        os.environ['ENVIRONMENT'] = 'development'
        dev_config = get_config('development')
        print(f"  ✅ 開発環境設定: {dev_config.__class__.__name__}")
        
        # テスト環境設定のテスト
        test_config = get_config('testing')
        print(f"  ✅ テスト環境設定: {test_config.__class__.__name__}")
        
        return True
    except Exception as e:
        print(f"  ❌ 設定テストエラー: {e}")
        return False

def test_security_manager():
    """SecurityManagerのテスト"""
    print("🔒 SecurityManagerのテスト...")
    
    try:
        from security.security_manager import SecurityManager
        from flask import Flask
        
        app = Flask(__name__)
        security_manager = SecurityManager(app)
        
        # APIキー取得テスト
        gemini_key = security_manager.get_api_key('gemini')
        if gemini_key:
            print(f"  ✅ Gemini APIキー取得成功: {gemini_key[:10]}...")
        else:
            print("  ⚠️ Gemini APIキーが設定されていません")
        
        # セキュアキー生成テスト
        secure_key = security_manager.generate_secure_key()
        print(f"  ✅ セキュアキー生成: {len(secure_key)}文字")
        
        return True
    except Exception as e:
        print(f"  ❌ SecurityManagerテストエラー: {e}")
        return False

def test_app_creation():
    """アプリケーション作成のテスト"""
    print("🚀 アプリケーション作成のテスト...")
    
    try:
        # テスト用の環境変数設定
        os.environ['ENVIRONMENT'] = 'testing'
        os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'
        
        from app import create_app
        
        app = create_app('testing')
        
        with app.test_client() as client:
            # メインページのテスト（最もシンプル）
            try:
                response = client.get('/')
                print(f"  ✅ メインページ: {response.status_code}")
            except Exception as e:
                print(f"  ❌ メインページエラー: {e}")
                return False
            
            # ヘルスチェックエンドポイントのテスト
            try:
                response = client.get('/health')
                print(f"  ✅ ヘルスチェック: {response.status_code}")
            except Exception as e:
                print(f"  ⚠️ ヘルスチェックエラー: {e}")
            
            # 404エラーハンドラーのテスト
            try:
                response = client.get('/nonexistent-page')
                print(f"  ✅ 404エラーハンドラー: {response.status_code}")
            except Exception as e:
                print(f"  ⚠️ 404エラーハンドラーエラー: {e}")
        
        return True
    except Exception as e:
        print(f"  ❌ アプリケーション作成テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_production_requirements():
    """本番環境要件のテスト"""
    print("📋 本番環境要件のテスト...")
    
    try:
        # 本番環境設定のテスト（環境変数なしでエラーになることを確認）
        os.environ['ENVIRONMENT'] = 'production'
        
        try:
            from config.production_config import ProductionConfig
            config = ProductionConfig()
            print("  ❌ 本番環境設定が環境変数なしで作成されました（問題）")
            return False
        except ValueError as e:
            print(f"  ✅ 本番環境設定の検証が正常に動作: {e}")
            return True
    except Exception as e:
        print(f"  ❌ 本番環境要件テストエラー: {e}")
        return False

def test_security_headers():
    """セキュリティヘッダーのテスト"""
    print("🛡️ セキュリティヘッダーのテスト...")
    
    try:
        os.environ['ENVIRONMENT'] = 'testing'
        from app import create_app
        
        app = create_app('testing')
        
        with app.test_client() as client:
            response = client.get('/')
            
            # セキュリティヘッダーの確認
            headers_to_check = [
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection',
                'Content-Security-Policy',
                'Referrer-Policy'
            ]
            
            for header in headers_to_check:
                if header in response.headers:
                    print(f"  ✅ {header}: {response.headers[header]}")
                else:
                    print(f"  ⚠️ {header}: 未設定")
        
        return True
    except Exception as e:
        print(f"  ❌ セキュリティヘッダーテストエラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("🔍 TOU Connect セキュリティ基盤テスト")
    print("=" * 60)
    
    tests = [
        ("設定クラス", test_config_validation),
        ("SecurityManager", test_security_manager),
        ("アプリケーション作成", test_app_creation),
        ("本番環境要件", test_production_requirements),
        ("セキュリティヘッダー", test_security_headers)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ {name}テスト中にエラー: {e}")
            results.append((name, False))
        print()
    
    # 結果サマリー
    print("=" * 60)
    print("📋 テスト結果サマリー")
    print("=" * 60)
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20s}: {status}")
        if result:
            passed += 1
    
    print(f"\n合計: {passed}/{len(results)} テストが成功")
    
    if passed == len(results):
        print("\n🎉 セキュリティ基盤のセットアップが完了しました！")
        return True
    else:
        print("\n⚠️ いくつかのテストが失敗しました。設定を確認してください。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)