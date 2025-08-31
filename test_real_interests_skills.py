#!/usr/bin/env python3
"""
実際の分析データから興味・スキルを抽出するテスト
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.database_manager import DatabaseManager
from repositories.user_repository import UserRepository
from repositories.analysis_repository import AnalysisRepository
from repositories.interests_skills_repository import InterestsSkillsRepository

def test_real_interests_skills_extraction():
    """実際のデータで興味・スキル抽出テスト"""
    print("🎯 実際データでの興味・スキル抽出テスト開始")
    
    # データベース準備
    db = DatabaseManager("tou_connect.db")
    user_repo = UserRepository(db)
    analysis_repo = AnalysisRepository(db)
    interests_skills_repo = InterestsSkillsRepository(db)
    
    try:
        # 1. 既存ユーザーと分析結果を取得
        print("👤 既存データ確認中...")
        user = user_repo.get_user_by_username("ike3don3")
        if not user:
            print("❌ ユーザーが見つかりません")
            return False
        
        analysis = analysis_repo.get_latest_analysis(user['id'])
        if not analysis:
            print("❌ 分析結果が見つかりません")
            return False
        
        print(f"✅ データ確認完了: {user['name']} (@{user['twitter_username']})")
        print(f"   分析ID: {analysis['id']}")
        
        # 2. 分析結果から興味・スキルを抽出
        print("🔍 興味・スキル抽出中...")
        
        # 生の分析データを再構築
        analysis_data = {
            'analysis': analysis['raw_analysis_data'],
            'bio': user['bio'],
            'major_field': analysis['major_field'],
            'learning_style': analysis['learning_style'],
            'university_relation': analysis['university_relation']
        }
        
        interests_count, skills_count = interests_skills_repo.extract_and_save_interests_skills(
            user['id'], analysis_data
        )
        
        print(f"✅ 抽出完了: 興味 {interests_count}件, スキル {skills_count}件")
        
        # 3. 抽出された興味・スキルを表示
        print("\n📚 抽出された興味:")
        interests = interests_skills_repo.get_user_interests(user['id'])
        for interest in interests:
            print(f"   - {interest['interest_name']} ({interest['interest_category']})")
            print(f"     信頼度: {interest['confidence_score']:.2f}, ソース: {interest['source']}")
        
        print("\n💻 抽出されたスキル:")
        skills = interests_skills_repo.get_user_skills(user['id'])
        for skill in skills:
            print(f"   - {skill['skill_name']} ({skill['skill_category']}, {skill['skill_level']})")
            print(f"     信頼度: {skill['confidence_score']:.2f}, ソース: {skill['source']}")
        
        # 4. 統計情報を表示
        print("\n📊 統計情報:")
        interest_stats = interests_skills_repo.get_interest_statistics()
        skill_stats = interests_skills_repo.get_skill_statistics()
        
        print("人気の興味ランキング:")
        for i, item in enumerate(interest_stats['popular_interests'][:5], 1):
            print(f"   {i}. {item['interest_name']}: {item['user_count']}人 (平均信頼度: {item['avg_confidence']:.2f})")
        
        print("人気のスキルランキング:")
        for i, item in enumerate(skill_stats['popular_skills'][:5], 1):
            print(f"   {i}. {item['skill_name']}: {item['user_count']}人 (平均信頼度: {item['avg_confidence']:.2f})")
        
        print("興味カテゴリ分布:")
        for cat in interest_stats['interest_categories']:
            print(f"   - {cat['interest_category']}: {cat['count']}件")
        
        print("スキルカテゴリ分布:")
        for cat in skill_stats['skill_categories']:
            print(f"   - {cat['skill_category']}: {cat['count']}件")
        
        # 5. 完全プロフィール表示
        print("\n" + "=" * 70)
        print(f"🎓 @{user['twitter_username']} の完全学習プロフィール")
        print("=" * 70)
        
        print("【基本情報】")
        print(f"名前: {user['name']}")
        print(f"大学: 東京通信大学 6期生")
        print(f"専攻: {analysis['major_field']}")
        print(f"所在地: {user['location']}")
        print(f"フォロワー: {user['followers_count']:,}")
        
        print("\n【学習プロフィール】")
        print(f"大学関係: {analysis['university_relation']}")
        print(f"関係性: {analysis['relation_type']}")
        print(f"性格特徴: {analysis['personality_traits']}")
        print(f"学習スタイル: {analysis['learning_style']}")
        print(f"協働可能性: {analysis['collaboration_potential']}")
        
        print("\n【興味分野】")
        for interest in interests:
            confidence_bar = "★" * int(interest['confidence_score'] * 5)
            print(f"   {interest['interest_name']} ({interest['interest_category']}) {confidence_bar}")
        
        print("\n【技術スキル】")
        for skill in skills:
            confidence_bar = "★" * int(skill['confidence_score'] * 5)
            print(f"   {skill['skill_name']} ({skill['skill_level']}) {confidence_bar}")
        
        print("=" * 70)
        
        print("🎉 実際データでの興味・スキル抽出テスト成功！")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close_connection()

def test_matching_potential():
    """マッチング可能性のテスト"""
    print("\n🤝 マッチング可能性テスト開始")
    
    db = DatabaseManager("tou_connect.db")
    interests_skills_repo = InterestsSkillsRepository(db)
    
    try:
        # 共通興味・スキルでの検索テスト
        print("🔍 共通興味・スキル検索テスト:")
        
        # プログラミングに興味がある人を検索
        programming_users = interests_skills_repo.find_users_by_interest("プログラミング")
        print(f"プログラミングに興味がある人: {len(programming_users)}人")
        
        # Pythonスキルを持つ人を検索
        python_users = interests_skills_repo.find_users_by_skill("Python")
        print(f"Pythonスキルを持つ人: {len(python_users)}人")
        
        # Web開発に興味がある人を検索
        web_users = interests_skills_repo.find_users_by_interest("Web")
        print(f"Web開発に興味がある人: {len(web_users)}人")
        
        print("🎉 マッチング可能性テスト完了")
        
    except Exception as e:
        print(f"❌ マッチングテストエラー: {e}")
    finally:
        db.close_connection()

if __name__ == "__main__":
    success = test_real_interests_skills_extraction()
    
    if success:
        test_matching_potential()
    
    print("\n📋 興味・スキル管理機能テスト完了")
    print("✅ 学友マッチングの基盤データが整いました！")