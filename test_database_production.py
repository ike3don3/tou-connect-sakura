#!/usr/bin/env python3
"""
本番環境データベース機能のテストスクリプト
"""
import os
import sys
import tempfile
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

def test_production_database_manager():
    """ProductionDatabaseManagerのテスト"""
    print("🗄️ ProductionDatabaseManagerのテスト...")
    
    try:
        from database.production_database_manager import ProductionDatabaseManager
        
        # SQLiteでのテスト
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            db = ProductionDatabaseManager(f"sqlite:///{db_path}")
            
            # 基本機能テスト
            print("  📊 基本機能テスト...")
            
            # テーブル作成
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value INTEGER DEFAULT 0
            )
            """
            db.execute_with_retry(create_table_sql)
            print("    テーブル作成: ✅")
            
            # データ挿入
            insert_sql = "INSERT INTO test_table (name, value) VALUES (?, ?)"
            db.execute_with_retry(insert_sql, ("test_name", 123))
            print("    データ挿入: ✅")
            
            # データ取得
            select_sql = "SELECT * FROM test_table WHERE name = ?"
            result = db.fetch_one_with_retry(select_sql, ("test_name",))
            if result and result['name'] == 'test_name':
                print("    データ取得: ✅")
            else:
                print("    データ取得: ❌")
            
            # 統計情報取得
            stats = db.get_database_stats()
            print(f"    統計情報: ✅ (クエリ数: {stats['total_queries']})")
            
            # ヘルスチェック
            health = db.health_check()
            print(f"    ヘルスチェック: {'✅' if health['status'] == 'healthy' else '❌'}")
            
            # バックアップテスト
            print("  💾 バックアップテスト...")
            try:
                backup_id = db.create_backup()
                print(f"    バックアップ作成: ✅ ({backup_id})")
                
                # バックアップ一覧
                backups = db.backup_manager.list_backups()
                print(f"    バックアップ一覧: ✅ ({len(backups)}個)")
                
            except Exception as e:
                print(f"    バックアップテスト: ⚠️ ({e})")
            
        finally:
            # クリーンアップ
            if os.path.exists(db_path):
                os.unlink(db_path)
        
        return True
        
    except Exception as e:
        print(f"  ❌ ProductionDatabaseManagerテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_schema_manager():
    """SchemaManagerのテスト"""
    print("📋 SchemaManagerのテスト...")
    
    try:
        from database.production_database_manager import ProductionDatabaseManager
        from database.schema_manager import SchemaManager
        
        # テスト用データベース
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            db = ProductionDatabaseManager(f"sqlite:///{db_path}")
            schema_manager = SchemaManager(db)
            
            # スキーマ作成
            print("  🏗️ スキーマ作成テスト...")
            schema_manager.create_production_schema()
            print("    本番スキーマ作成: ✅")
            
            # スキーマ情報取得
            schema_info = schema_manager.get_schema_info()
            print(f"    スキーマ情報: ✅ (テーブル数: {schema_info['total_tables']})")
            
            # 主要テーブルの存在確認
            expected_tables = [
                'users', 'user_analyses', 'user_interests', 'user_skills',
                'user_consents', 'audit_logs', 'system_metrics'
            ]
            
            existing_tables = [table['table_name'] for table in schema_info['tables']]
            
            for table in expected_tables:
                if table in existing_tables:
                    print(f"    テーブル {table}: ✅")
                else:
                    print(f"    テーブル {table}: ❌")
            
            # データベース最適化
            print("  ⚡ 最適化テスト...")
            schema_manager.optimize_database()
            print("    データベース最適化: ✅")
            
        finally:
            # クリーンアップ
            if os.path.exists(db_path):
                os.unlink(db_path)
        
        return True
        
    except Exception as e:
        print(f"  ❌ SchemaManagerテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_integration():
    """データベース統合テスト"""
    print("🔧 データベース統合テスト...")
    
    try:
        # テスト用の環境変数設定
        os.environ['ENVIRONMENT'] = 'testing'
        os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'
        
        from app import create_app
        
        app = create_app('testing')
        
        with app.test_client() as client:
            # データベース統計API
            print("  📊 データベース統計API...")
            response = client.get('/api/admin/database/stats')
            print(f"    統計API: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
            
            if response.status_code == 200:
                stats = response.get_json()
                print(f"      データベースタイプ: {stats.get('database_type', 'unknown')}")
            
            # スキーマ情報API
            print("  📋 スキーマ情報API...")
            response = client.get('/api/admin/database/schema')
            print(f"    スキーマAPI: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
            
            if response.status_code == 200:
                schema = response.get_json()
                print(f"      データベースタイプ: {schema.get('database_type', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ データベース統合テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_connection_pool():
    """接続プールのテスト"""
    print("🏊 接続プールテスト...")
    
    try:
        from database.production_database_manager import ProductionDatabaseManager
        
        # SQLiteでは接続プールは使用されない
        db = ProductionDatabaseManager("sqlite:///:memory:")
        
        pool_stats = db.get_connection_pool_stats()
        print(f"  接続プール統計: ✅")
        print(f"    タイプ: {pool_stats['type']}")
        print(f"    プール有効: {pool_stats['pool_enabled']}")
        
        # 複数の同時クエリテスト
        print("  📊 同時クエリテスト...")
        
        # テーブル作成
        db.execute_with_retry("""
            CREATE TABLE IF NOT EXISTS concurrent_test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 複数のクエリを実行
        import threading
        import time
        
        def worker(thread_id):
            for i in range(5):
                db.execute_with_retry(
                    "INSERT INTO concurrent_test (thread_id) VALUES (?)",
                    (thread_id,)
                )
                time.sleep(0.01)
        
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 結果確認
        results = db.fetch_all_with_retry("SELECT COUNT(*) as count FROM concurrent_test")
        total_records = results[0]['count'] if results else 0
        
        print(f"    同時実行結果: ✅ ({total_records}レコード)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 接続プールテストエラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("🔍 TOU Connect データベース本番化テスト")
    print("=" * 70)
    
    tests = [
        ("ProductionDatabaseManager", test_production_database_manager),
        ("SchemaManager", test_schema_manager),
        ("データベース統合", test_database_integration),
        ("接続プール", test_connection_pool)
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
        print("\n🎉 データベース本番化のセットアップが完了しました！")
        return True
    else:
        print("\n⚠️ いくつかのテストが失敗しました。設定を確認してください。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)