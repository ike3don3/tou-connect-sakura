#!/usr/bin/env python3
"""
本番環境インフラ機能のテストスクリプト
"""
import os
import sys
import json
import time
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

def test_health_check_manager():
    """HealthCheckManagerのテスト"""
    print("🏥 HealthCheckManagerのテスト...")
    
    try:
        from database.database_manager import DatabaseManager
        from infrastructure.health_check_manager import HealthCheckManager
        
        # テスト用データベース
        db = DatabaseManager(":memory:")
        health_manager = HealthCheckManager(db)
        
        # 包括的ヘルスチェック
        print("  📊 包括的ヘルスチェック...")
        health_status = health_manager.get_comprehensive_health_status()
        
        print(f"    全体ステータス: {health_status['status']}")
        print(f"    レスポンス時間: {health_status['response_time_ms']}ms")
        print(f"    チェック項目数: {len(health_status.get('checks', {}))}")
        
        # 個別チェック
        print("  🔍 個別チェック...")
        
        # データベースチェック
        db_check = health_manager.check_database_connection()
        print(f"    データベース: {db_check['status']} ({db_check.get('response_time_ms', 0)}ms)")
        
        # システムリソースチェック
        resource_check = health_manager.check_system_resources()
        print(f"    システムリソース: {resource_check['status']}")
        print(f"      CPU: {resource_check.get('cpu_percent', 0)}%")
        print(f"      メモリ: {resource_check.get('memory_percent', 0)}%")
        
        # ディスク容量チェック
        disk_check = health_manager.check_disk_space()
        print(f"    ディスク容量: {disk_check['status']} ({disk_check.get('disk_percent', 0)}%)")
        
        # Readiness/Liveness チェック
        readiness = health_manager.get_readiness_status()
        liveness = health_manager.get_liveness_status()
        print(f"    Readiness: {readiness['status']}")
        print(f"    Liveness: {liveness['status']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ HealthCheckManagerテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logging_manager():
    """LoggingManagerのテスト"""
    print("📝 LoggingManagerのテスト...")
    
    try:
        from infrastructure.logging_manager import LoggingManager, get_logger, log_user_action, log_security_event
        
        # ログマネージャーの初期化
        log_manager = LoggingManager('test_app')
        
        # ロガーの取得
        logger = get_logger('test_logger')
        print("  ✅ ロガー取得成功")
        
        # 各種ログのテスト
        print("  📋 各種ログテスト...")
        
        # 基本ログ
        logger.info("テスト情報ログ")
        logger.warning("テスト警告ログ")
        logger.error("テストエラーログ")
        
        # ユーザーアクションログ
        log_user_action(1, 'test_action', {'detail': 'test'})
        print("    ユーザーアクションログ: ✅")
        
        # セキュリティイベントログ
        log_security_event('test_security_event', 'medium', {'source': 'test'})
        print("    セキュリティイベントログ: ✅")
        
        # パフォーマンスメトリクスログ
        log_manager.log_performance_metric(logger, 'test_metric', 123.45, 'ms')
        print("    パフォーマンスメトリクスログ: ✅")
        
        # APIリクエストログ
        log_manager.log_api_request(logger, 'GET', '/test', 200, 45.67)
        print("    APIリクエストログ: ✅")
        
        return True
        
    except Exception as e:
        print(f"  ❌ LoggingManagerテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_infrastructure_integration():
    """インフラ統合テスト"""
    print("🔧 インフラ統合テスト...")
    
    try:
        # テスト用の環境変数設定
        os.environ['ENVIRONMENT'] = 'testing'
        os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'
        
        from app import create_app
        
        app = create_app('testing')
        
        with app.test_client() as client:
            # ヘルスチェックエンドポイント
            print("  🏥 ヘルスチェックエンドポイント...")
            
            response = client.get('/health')
            print(f"    /health: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
            
            if response.status_code == 200:
                health_data = response.get_json()
                print(f"      ステータス: {health_data.get('status', 'unknown')}")
                print(f"      チェック数: {len(health_data.get('checks', {}))}")
            
            # Readiness probe
            response = client.get('/health/ready')
            print(f"    /health/ready: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
            
            # Liveness probe
            response = client.get('/health/live')
            print(f"    /health/live: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
            
            # 通常のエンドポイント（ログテスト）
            print("  📝 ログ統合テスト...")
            response = client.get('/')
            print(f"    メインページ: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
            
            # 404エラーハンドラー
            response = client.get('/nonexistent')
            print(f"    404エラーハンドラー: {response.status_code} {'✅' if response.status_code == 404 else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ インフラ統合テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """エラーハンドリングのテスト"""
    print("⚠️ エラーハンドリングテスト...")
    
    try:
        os.environ['ENVIRONMENT'] = 'testing'
        from app import create_app
        
        app = create_app('testing')
        
        with app.test_client() as client:
            # 404エラー
            response = client.get('/this-does-not-exist')
            print(f"    404エラー: {response.status_code} {'✅' if response.status_code == 404 else '❌'}")
            
            # 存在しないAPIエンドポイント
            response = client.post('/api/nonexistent')
            print(f"    存在しないAPI: {response.status_code} {'✅' if response.status_code == 404 else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ エラーハンドリングテストエラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("🔍 TOU Connect 本番環境インフラテスト")
    print("=" * 70)
    
    tests = [
        ("HealthCheckManager", test_health_check_manager),
        ("LoggingManager", test_logging_manager),
        ("インフラ統合", test_infrastructure_integration),
        ("エラーハンドリング", test_error_handling)
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
    print("=" * 70)
    print("📋 テスト結果サマリー")
    print("=" * 70)
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:30s}: {status}")
        if result:
            passed += 1
    
    print(f"\n合計: {passed}/{len(results)} テストが成功")
    
    if passed == len(results):
        print("\n🎉 本番環境インフラのセットアップが完了しました！")
        return True
    else:
        print("\n⚠️ いくつかのテストが失敗しました。設定を確認してください。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)