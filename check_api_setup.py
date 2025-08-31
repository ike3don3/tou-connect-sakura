#!/usr/bin/env python3
"""
Twitter API 設定確認ツール
"""
import os
from dotenv import load_dotenv
from twitter_api import TwitterAPI

def check_api_setup():
    """API設定の確認"""
    print("🔧 Twitter API 設定確認\n")
    
    # 環境変数の確認
    load_dotenv()
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    
    print("1. 環境変数の確認:")
    if bearer_token:
        print(f"   ✅ TWITTER_BEARER_TOKEN: {bearer_token[:20]}...")
        
        # 実際のAPI接続テスト
        print("\n2. API接続テスト:")
        try:
            api = TwitterAPI()
            if api.client:
                print("   ✅ Twitter API クライアント初期化成功")
                
                # 簡単なテスト（自分のアカウント情報取得）
                print("\n3. 実際のデータ取得テスト:")
                test_user = api.get_user_by_username("twitter")  # 公式アカウントでテスト
                
                if test_user:
                    print("   ✅ 実際のTwitterデータ取得成功!")
                    print(f"   📊 テストアカウント: @{test_user['username']}")
                    print(f"   👥 フォロワー数: {test_user['followers_count']:,}")
                    print("\n🎉 Twitter API が正常に動作しています!")
                    return True
                else:
                    print("   ❌ データ取得に失敗")
                    return False
            else:
                print("   ❌ API クライアント初期化失敗")
                return False
                
        except Exception as e:
            print(f"   ❌ API接続エラー: {e}")
            return False
    else:
        print("   ❌ TWITTER_BEARER_TOKEN が設定されていません")
        print("\n📝 設定手順:")
        print("   1. https://developer.twitter.com/en/portal/dashboard でAPI申請")
        print("   2. Bearer Token を取得")
        print("   3. .env ファイルに以下を追加:")
        print("      TWITTER_BEARER_TOKEN=your_actual_token_here")
        print("\n📖 詳細は TWITTER_API_SETUP.md を参照してください")
        return False

def main():
    """メイン実行"""
    if check_api_setup():
        print("\n✨ 次のステップ:")
        print("   - python app.py でWebアプリを起動")
        print("   - 実際のTwitterアカウントで分析テスト")
    else:
        print("\n🔄 現在の状況:")
        print("   - モックデータで開発継続可能")
        print("   - API設定後に実データに切り替わります")

if __name__ == "__main__":
    main()