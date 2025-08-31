#!/usr/bin/env python3
"""
Twitter API 連携のテスト
"""
from twitter_api import get_twitter_client
import json

def test_twitter_api():
    """Twitter API のテスト"""
    print("🐦 Twitter API 連携テスト開始\n")
    
    # クライアント取得
    client = get_twitter_client()
    
    # テストアカウント
    test_accounts = ["ike3don3", "elonmusk", "openai"]
    
    for username in test_accounts:
        print(f"📊 @{username} をテスト中...")
        print("-" * 50)
        
        try:
            data = client.get_full_user_data(username)
            
            if data:
                user_info = data['user_info']
                tweets = data['tweets']
                
                print(f"✅ ユーザー情報取得成功:")
                print(f"  名前: {user_info['name']}")
                print(f"  自己紹介: {user_info['description'][:100]}...")
                print(f"  フォロワー: {user_info['followers_count']:,}")
                print(f"  ツイート数: {user_info['tweet_count']:,}")
                print(f"  最新ツイート数: {len(tweets)}")
                
                if tweets:
                    print(f"  最新ツイート例: {tweets[0]['text'][:80]}...")
                
                print()
            else:
                print(f"❌ @{username} のデータ取得に失敗")
                print()
                
        except Exception as e:
            print(f"❌ エラー: {e}")
            print()
    
    print("🎯 テスト完了!")

if __name__ == "__main__":
    test_twitter_api()