#!/usr/bin/env python3
"""
特定のアカウントでのクイックテスト
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import analyze_twitter_account

def test_specific_account(username):
    """特定のアカウントをテスト"""
    print(f"🔍 @{username} の分析テスト開始...\n")
    
    try:
        result = analyze_twitter_account(username)
        
        print("=" * 60)
        print(f"📊 @{result['username']} の分析結果")
        print("=" * 60)
        
        print("\n【アカウント情報】")
        account = result['account_data']
        print(f"名前: {account['name']}")
        print(f"自己紹介: {account['bio']}")
        print(f"フォロワー: {account['followers']} | フォロー: {account['following']}")
        
        print("\n【AI分析結果】")
        print(result['analysis'])
        
        print("\n" + "=" * 60)
        print("✅ 分析完了！")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ エラー: {e}")
        print("詳細なエラー情報:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    username = "ike3don3"
    test_specific_account(username)