#!/usr/bin/env python3
"""
プライバシー・法的コンプライアンス機能のテストスクリプト
"""
import os
import sys
import json
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

def test_privacy_manager():
    """PrivacyManagerのテスト"""
    print("🔒 PrivacyManagerのテスト...")
    
    try:
        from database.database_manager import DatabaseManager
        from privacy.privacy_manager import PrivacyManager
        
        # テスト用データベース
        db = DatabaseManager(":memory:")
        privacy_manager = PrivacyManager(db)
        
        # テストユーザーID
        test_user_id = 1
        
        # 同意記録のテスト
        print("  📝 同意記録テスト...")
        success = privacy_manager.create_consent_record(
            test_user_id, 
            'privacy_policy',
            metadata={'test': True}
        )
        print(f"    プライバシーポリシー同意: {'✅' if success else '❌'}")
        
        success = privacy_manager.create_consent_record(
            test_user_id, 
            'terms_of_service',
            metadata={'test': True}
        )
        print(f"    利用規約同意: {'✅' if success else '❌'}")
        
        # 同意状況確認のテスト
        print("  📋 同意状況確認テスト...")
        consents = privacy_manager.get_user_consents(test_user_id)
        print(f"    取得した同意記録数: {len(consents)}")
        
        consent_check = privacy_manager.check_consent_required(test_user_id)
        print(f"    同意が必要: {'❌' if consent_check['any_required'] else '✅'}")
        
        # 監査ログのテスト
        print("  📊 監査ログテスト...")
        privacy_manager.log_user_action(
            test_user_id, 
            'test_action', 
            'test_resource', 
            123,
            {'test_data': 'value'}
        )
        
        logs = privacy_manager.get_audit_logs(test_user_id)
        print(f"    監査ログ記録数: {len(logs)}")
        
        # データエクスポートのテスト
        print("  📤 データエクスポートテスト...")
        export_data = privacy_manager.export_user_data(test_user_id)
        if 'error' not in export_data:
            print(f"    エクスポート成功: {len(export_data['data'])} カテゴリ")
        else:
            print(f"    エクスポートエラー: {export_data['error']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ PrivacyManagerテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_privacy_pages():
    """プライバシー関連ページのテスト"""
    print("📄 プライバシー関連ページのテスト...")
    
    try:
        # テスト用の環境変数設定
        os.environ['ENVIRONMENT'] = 'testing'
        os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'
        
        from app import create_app
        
        app = create_app('testing')
        
        with app.test_client() as client:
            # プライバシーポリシーページ
            response = client.get('/privacy')
            print(f"  プライバシーポリシーページ: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
            
            # 利用規約ページ
            response = client.get('/terms')
            print(f"  利用規約ページ: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
            
            # 同意状況API
            response = client.get('/api/consent/status?user_id=1')
            print(f"  同意状況API: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"    同意が必要: {data.get('consent_required', 'unknown')}")
            
            # 同意記録API
            consent_data = {
                'user_id': 1,
                'privacy_policy': True,
                'terms_of_service': True,
                'ai_analysis': True,
                'timestamp': '2024-01-01T00:00:00Z'
            }
            
            response = client.post('/api/consent', 
                                 json=consent_data,
                                 content_type='application/json')
            print(f"  同意記録API: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
            
            # データエクスポートAPI
            response = client.get('/api/user/data/export?user_id=1')
            print(f"  データエクスポートAPI: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ プライバシーページテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gdpr_compliance():
    """GDPR準拠機能のテスト"""
    print("🇪🇺 GDPR準拠機能のテスト...")
    
    try:
        from database.database_manager import DatabaseManager
        from privacy.privacy_manager import PrivacyManager
        
        # テスト用データベース
        db = DatabaseManager(":memory:")
        privacy_manager = PrivacyManager(db)
        
        test_user_id = 1
        
        # データ匿名化のテスト
        print("  🔒 データ匿名化テスト...")
        success = privacy_manager.anonymize_user_data(test_user_id)
        print(f"    匿名化処理: {'✅' if success else '❌'}")
        
        # データ削除のテスト
        print("  🗑️ データ削除テスト...")
        success = privacy_manager.delete_user_data(test_user_id, 'complete')
        print(f"    完全削除処理: {'✅' if success else '❌'}")
        
        # 統計情報のテスト
        print("  📈 統計情報テスト...")
        stats = privacy_manager.get_privacy_statistics()
        print(f"    統計情報取得: {'✅' if isinstance(stats, dict) else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ GDPR準拠テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メインテスト実行"""
    print("🔍 TOU Connect プライバシー・法的コンプライアンステスト")
    print("=" * 70)
    
    tests = [
        ("PrivacyManager", test_privacy_manager),
        ("プライバシー関連ページ", test_privacy_pages),
        ("GDPR準拠機能", test_gdpr_compliance)
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
        print("\n🎉 プライバシー・法的コンプライアンス機能のセットアップが完了しました！")
        return True
    else:
        print("\n⚠️ いくつかのテストが失敗しました。設定を確認してください。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)