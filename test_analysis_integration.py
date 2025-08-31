#!/usr/bin/env python3
"""
AI分析結果 → Database 統合テスト
実際のGemini AI分析結果をデータベースに保存
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.database_manager import DatabaseManager
from repositories.user_repository import UserRepository
from repositories.analysis_repository import AnalysisRepository
from app import analyze_twitter_account

def test_ai_analysis_to_database():
    """AI分析 → Database の完全フロー"""
    print("🧠 AI分析 → Database 統合テスト開始")
    
    # データベース準備
    db = DatabaseManager("tou_connect.db")
    user_repo = UserRepository(db)
    analysis_repo = AnalysisRepository(db)
    
    try:
        # 1. 既存ユーザーを確認
        print("👤 既存ユーザー確認中...")
        user = user_repo.get_user_by_username("ike3don3")
        
        if not user:
            print("❌ ユーザーが見つかりません。先にユーザーを作成してください。")
            return False
        
        print(f"✅ ユーザー確認: {user['name']} (@{user['twitter_username']})")
        user_id = user['id']
        
        # 2. AI分析を実行
        print("🤖 AI分析実行中...")
        analysis_result = analyze_twitter_account("ike3don3")
        
        if analysis_result.get('status') != 'success':
            print(f"❌ AI分析失敗: {analysis_result.get('error', '不明なエラー')}")
            return False
        
        print("✅ AI分析完了")
        print(f"   分析対象: @{analysis_result['username']}")
        
        # 3. 分析結果をデータベースに保存
        print("💾 分析結果をデータベースに保存中...")
        analysis_id = analysis_repo.save_analysis(user_id, analysis_result)
        print(f"✅ 分析結果保存完了: 分析ID {analysis_id}")
        
        # 4. 保存された分析結果を確認
        print("🔍 保存データ確認中...")
        saved_analysis = analysis_repo.get_latest_analysis(user_id)
        
        if saved_analysis:
            print("✅ 保存確認成功:")
            print(f"   大学関係: {saved_analysis['university_relation']}")
            print(f"   関係性: {saved_analysis['relation_type']}")
            print(f"   専攻分野: {saved_analysis['major_field']}")
            print(f"   信頼度: {saved_analysis['analysis_confidence']:.2f}")
        else:
            print("❌ 保存データが見つかりません")
            return False
        
        # 5. 統計情報を表示
        print("📊 分析統計情報:")
        stats = analysis_repo.get_analysis_statistics()
        print(f"   総分析数: {stats['total_analyses']}")
        print(f"   平均信頼度: {stats['average_confidence']:.2f}")
        
        # 大学関係者分布
        print("   大学関係者分布:")
        for dist in stats['university_relation_distribution']:
            print(f"     {dist['university_relation']}: {dist['count']}件")
        
        # 専攻分野分布
        print("   専攻分野分布:")
        for dist in stats['major_field_distribution']:
            print(f"     {dist['major_field']}: {dist['count']}件")
        
        print("🎉 AI分析 → Database 統合テスト成功！")
        return True
        
    except Exception as e:
        print(f"❌ 統合テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close_connection()

def test_analysis_search():
    """分析結果検索機能のテスト"""
    print("\n🔍 分析結果検索テスト開始")
    
    db = DatabaseManager("tou_connect.db")
    analysis_repo = AnalysisRepository(db)
    
    try:
        # 1. 大学関係者検索
        print("📚 大学関係者検索:")
        high_relation_users = analysis_repo.get_users_by_criteria({'university_relation': '高'})
        print(f"   大学関係者（高）: {len(high_relation_users)}件")
        
        for user in high_relation_users:
            print(f"     - @{user['twitter_username']} ({user['name']})")
            print(f"       専攻: {user['major_field']}, 信頼度: {user['analysis_confidence']:.2f}")
        
        # 2. 専攻分野検索
        print("\n💻 情報学専攻検索:")
        cs_users = analysis_repo.get_users_by_criteria({'major_field': '情報学'})
        print(f"   情報学専攻: {len(cs_users)}件")
        
        # 3. 高信頼度分析検索
        print("\n⭐ 高信頼度分析検索:")
        high_confidence_users = analysis_repo.get_users_by_criteria({'min_confidence': 0.8})
        print(f"   高信頼度（0.8以上）: {len(high_confidence_users)}件")
        
        print("🎉 分析結果検索テスト完了")
        
    except Exception as e:
        print(f"❌ 検索テストエラー: {e}")
    finally:
        db.close_connection()

def display_complete_user_profile():
    """完全なユーザープロフィールを表示"""
    print("\n👤 完全ユーザープロフィール表示")
    
    db = DatabaseManager("tou_connect.db")
    user_repo = UserRepository(db)
    analysis_repo = AnalysisRepository(db)
    
    try:
        # ユーザー基本情報
        user = user_repo.get_user_by_username("ike3don3")
        if not user:
            print("❌ ユーザーが見つかりません")
            return
        
        # 分析結果
        analysis = analysis_repo.get_latest_analysis(user['id'])
        
        print("=" * 60)
        print(f"📋 @{user['twitter_username']} の完全プロフィール")
        print("=" * 60)
        
        print("【基本情報】")
        print(f"名前: {user['name']}")
        print(f"自己紹介: {user['bio']}")
        print(f"所在地: {user['location']}")
        print(f"フォロワー: {user['followers_count']:,}")
        print(f"フォロー: {user['following_count']:,}")
        print(f"ツイート数: {user['tweet_count']:,}")
        
        if analysis:
            print("\n【AI分析結果】")
            print(f"大学関係: {analysis['university_relation']}")
            print(f"関係性: {analysis['relation_type']}")
            print(f"専攻分野: {analysis['major_field']}")
            print(f"学習スタイル: {analysis['learning_style']}")
            print(f"協働可能性: {analysis['collaboration_potential']}")
            print(f"分析信頼度: {analysis['analysis_confidence']:.2f}")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ プロフィール表示エラー: {e}")
    finally:
        db.close_connection()

if __name__ == "__main__":
    # 統合テスト実行
    success = test_ai_analysis_to_database()
    
    if success:
        test_analysis_search()
        display_complete_user_profile()
    
    print("\n📋 AI分析統合テスト完了")
    print("次のステップ: 興味・スキル管理機能の実装")