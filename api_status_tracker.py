#!/usr/bin/env python3
"""
Twitter API 申請状況追跡ツール
"""
import os
from datetime import datetime
from dotenv import load_dotenv

def check_application_status():
    """申請状況の確認"""
    print("📋 Twitter API 申請状況チェック\n")
    
    # 環境変数確認
    load_dotenv()
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    
    if bearer_token and bearer_token != "your_actual_bearer_token_here":
        print("✅ API設定完了!")
        print(f"   Bearer Token: {bearer_token[:20]}...")
        
        # 実際のAPI接続テスト
        from twitter_api import TwitterAPI
        api = TwitterAPI()
        
        if api.client:
            print("✅ API接続成功!")
            
            # テスト用の公開アカウントで動作確認
            test_result = api.get_user_by_username("twitter")
            if test_result:
                print("✅ データ取得テスト成功!")
                print(f"   テストアカウント: @{test_result['username']}")
                print(f"   フォロワー数: {test_result['followers_count']:,}")
                
                print("\n🎉 Twitter API が正常に動作しています!")
                print("\n次のステップ:")
                print("   1. python app.py でWebアプリ起動")
                print("   2. 実際のアカウントで分析テスト")
                print("   3. データベース機能の実装")
                
                return "active"
            else:
                print("❌ データ取得テストに失敗")
                return "error"
        else:
            print("❌ API接続に失敗")
            return "error"
    else:
        print("⏳ API申請待ち状態")
        print("\n📝 申請手順:")
        print("   1. https://developer.twitter.com/en/portal/dashboard")
        print("   2. application_template.txt の内容を使用")
        print("   3. 承認後、Bearer Tokenを.envに設定")
        
        print("\n📊 現在の開発状況:")
        print("   ✅ モックデータでの動作確認完了")
        print("   ✅ AI分析機能実装完了")
        print("   ✅ Webアプリ基本機能完了")
        print("   ⏳ 実際のTwitterデータ取得待ち")
        
        return "pending"

def show_next_steps(status):
    """次のステップを表示"""
    print("\n" + "="*50)
    print("🎯 開発ロードマップ")
    print("="*50)
    
    if status == "active":
        print("Phase 1: ✅ Twitter API連携 (完了)")
        print("Phase 2: 🔄 データベース実装 (次のステップ)")
        print("Phase 3: ⏳ マッチング機能")
        print("Phase 4: ⏳ 可視化機能")
        print("Phase 5: ⏳ コミュニティ機能")
    elif status == "pending":
        print("Phase 1: 🔄 Twitter API申請中")
        print("Phase 2: ⏳ データベース実装")
        print("Phase 3: ⏳ マッチング機能")
        print("Phase 4: ⏳ 可視化機能")
        print("Phase 5: ⏳ コミュニティ機能")
        
        print("\n💡 申請待ちの間にできること:")
        print("   - データベース設計")
        print("   - マッチングアルゴリズム開発")
        print("   - UI/UX改善")
        print("   - テストケース拡充")
    else:
        print("Phase 1: ❌ Twitter API設定エラー")
        print("   → 設定を確認してください")

def main():
    """メイン実行"""
    print(f"🕐 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    status = check_application_status()
    show_next_steps(status)
    
    print(f"\n📞 サポート:")
    print("   - 申請に関する質問: API_APPLICATION_GUIDE.md")
    print("   - 技術的な問題: check_api_setup.py")
    print("   - 開発継続: モックデータで機能開発可能")

if __name__ == "__main__":
    main()