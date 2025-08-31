#!/usr/bin/env python3
"""
Twitter API + Database 統合テスト
実際のTwitterデータをデータベースに保存
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.database_manager import DatabaseManager
from repositories.user_repository import UserRepository
from twitter_api import get_twitter_client

def test_twitter_to_database():
    """Twitter API → Database の完全フロー"""
    print("🔄 Twitter API → Database 統合テスト開始")
    
    # データベース準備
    db = DatabaseManager("tou_connect.db")
    user_repo = UserRepository(db)
    
    # Twitter API クライアント
    twitter_client = get_twitter_client()
    
    try:
        # 1. 実際のTwitterデータを取得
        print("📡 Twitter データ取得中...")
        username = "ike3don3"
        twitter_data = twitter_client.get_full_user_data(username)
        
        if not twitter_data:
            print("❌ Twitterデータの取得に失敗")
            return False
        
        user_info = twitter_data['user_info']
        print(f"✅ @{user_info['username']} のデータを取得")
        print(f"   名前: {user_info['name']}")
        print(f"   フォロワー: {user_info['followers_count']:,}")
        
        # 2. データベースに保存
        print("💾 データベースに保存中...")
        user_id = user_repo.create_or_update_user(user_info)
        print(f"✅ ユーザーID {user_id} で保存完了")
        
        # 3. 保存されたデータを確認
        print("🔍 保存データ確認中...")
        saved_user = user_repo.get_user_by_id(user_id)
        print(f"✅ 保存確認: {saved_user['name']} (@{saved_user['twitter_username']})")
        
        # 4. 統計情報
        print("📊 データベース統計:")
        total_users = user_repo.get_user_count()
        print(f"   総ユーザー数: {total_users}")
        
        recent_users = user_repo.get_recent_users(5)
        print(f"   最近のユーザー: {len(recent_users)}件")
        for user in recent_users:
            print(f"     - @{user['twitter_username']} ({user['name']})")
        
        print("🎉 統合テスト成功！")
        return True
        
    except Exception as e:
        print(f"❌ 統合テストエラー: {e}")
        return False
    finally:
        db.close_connection()

def test_multiple_users():
    """複数ユーザーでのテスト"""
    print("\n👥 複数ユーザーテスト開始")
    
    db = DatabaseManager("tou_connect.db")
    user_repo = UserRepository(db)
    twitter_client = get_twitter_client()
    
    # テスト対象アカウント（東京通信大学関係者を想定）
    test_accounts = ["ike3don3", "elonmusk", "openai"]  # 実際のアカウント
    
    try:
        for username in test_accounts:
            print(f"\n🔍 @{username} を処理中...")
            
            twitter_data = twitter_client.get_full_user_data(username)
            if twitter_data:
                user_info = twitter_data['user_info']
                user_id = user_repo.create_or_update_user(user_info)
                print(f"✅ @{username} → ユーザーID {user_id}")
            else:
                print(f"❌ @{username} のデータ取得失敗")
        
        # 検索テスト
        print("\n🔍 検索機能テスト:")
        
        # 全ユーザー検索
        all_users = user_repo.search_users({})
        print(f"全ユーザー: {len(all_users)}件")
        
        # 条件検索
        tokyo_users = user_repo.search_users({'location': '東京'})
        print(f"東京在住: {len(tokyo_users)}件")
        
        verified_users = user_repo.search_users({'verified': True})
        print(f"認証済み: {len(verified_users)}件")
        
        print("🎉 複数ユーザーテスト完了")
        
    except Exception as e:
        print(f"❌ 複数ユーザーテストエラー: {e}")
    finally:
        db.close_connection()

if __name__ == "__main__":
    # 統合テスト実行
    success = test_twitter_to_database()
    
    if success:
        test_multiple_users()
    
    print("\n📋 テスト完了")
    print("次のステップ: AI分析結果の保存機能を実装")