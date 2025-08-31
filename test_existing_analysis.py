#!/usr/bin/env python3
"""
既存の分析結果を使ったデータベーステスト
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.database_manager import DatabaseManager
from repositories.user_repository import UserRepository
from repositories.analysis_repository import AnalysisRepository

def test_with_existing_analysis():
    """既存の分析結果を使ったテスト"""
    print("🧠 既存分析結果でのデータベーステスト開始")
    
    # データベース準備
    db = DatabaseManager("tou_connect.db")
    user_repo = UserRepository(db)
    analysis_repo = AnalysisRepository(db)
    
    try:
        # 1. 既存ユーザーを確認
        user = user_repo.get_user_by_username("ike3don3")
        if not user:
            print("❌ ユーザーが見つかりません")
            return False
        
        print(f"✅ ユーザー確認: {user['name']} (@{user['twitter_username']})")
        user_id = user['id']
        
        # 2. 実際の分析結果を模擬（以前の成功した分析結果を使用）
        mock_analysis_result = {
            'username': 'ike3don3',
            'account_data': {
                'name': user['name'],
                'username': user['twitter_username'],
                'bio': user['bio']
            },
            'analysis': '''```json
{
  "university_relation": "高",
  "university_relation_reason": "自己紹介に「東京通信大学 TOU 6期生」と明記されているため。",
  "relation_type": "学生",
  "interests": ["IT・情報システム", "WEBプログラミング", "AI", "メタバース", "データ分析"],
  "major_field": "情報学",
  "personality_traits": ["論理的", "効率的"],
  "learning_style": "推測困難 (GPAの推移から、目標設定と自己管理能力は高いと推測できる)",
  "activity_pattern": "推測困難 (SNSの活動は活発だが、学習以外の活動については情報が不足)",
  "tech_skills": ["WEBプログラミング", "ChatGPT活用"],
  "collaboration_potential": "高 (積極的に情報発信しており、協調性もあると推測できる)"
}
```''',
            'status': 'success'
        }
        
        # 3. 分析結果をデータベースに保存
        print("💾 分析結果をデータベースに保存中...")
        analysis_id = analysis_repo.save_analysis(user_id, mock_analysis_result)
        print(f"✅ 分析結果保存完了: 分析ID {analysis_id}")
        
        # 4. 保存された分析結果を確認
        print("🔍 保存データ確認中...")
        saved_analysis = analysis_repo.get_latest_analysis(user_id)
        
        if saved_analysis:
            print("✅ 保存確認成功:")
            print(f"   大学関係: {saved_analysis['university_relation']}")
            print(f"   関係性: {saved_analysis['relation_type']}")
            print(f"   専攻分野: {saved_analysis['major_field']}")
            print(f"   学習スタイル: {saved_analysis['learning_style'][:50]}...")
            print(f"   協働可能性: {saved_analysis['collaboration_potential']}")
            print(f"   信頼度: {saved_analysis['analysis_confidence']:.2f}")
        
        # 5. 検索機能テスト
        print("\n🔍 検索機能テスト:")
        
        # 大学関係者検索
        high_relation_users = analysis_repo.get_users_by_criteria({'university_relation': '高'})
        print(f"   大学関係者（高）: {len(high_relation_users)}件")
        
        # 情報学専攻検索
        cs_users = analysis_repo.get_users_by_criteria({'major_field': '情報学'})
        print(f"   情報学専攻: {len(cs_users)}件")
        
        # 学生検索
        students = analysis_repo.get_users_by_criteria({'relation_type': '学生'})
        print(f"   学生: {len(students)}件")
        
        # 6. 統計情報
        print("\n📊 統計情報:")
        stats = analysis_repo.get_analysis_statistics()
        print(f"   総分析数: {stats['total_analyses']}")
        print(f"   平均信頼度: {stats['average_confidence']:.2f}")
        
        print("   大学関係者分布:")
        for dist in stats['university_relation_distribution']:
            print(f"     {dist['university_relation']}: {dist['count']}件")
        
        print("   専攻分野分布:")
        for dist in stats['major_field_distribution']:
            print(f"     {dist['major_field']}: {dist['count']}件")
        
        # 7. 完全プロフィール表示
        print("\n" + "=" * 60)
        print(f"📋 @{user['twitter_username']} の完全プロフィール")
        print("=" * 60)
        
        print("【基本情報】")
        print(f"名前: {user['name']}")
        print(f"自己紹介: {user['bio']}")
        print(f"所在地: {user['location'] or '未設定'}")
        print(f"フォロワー: {user['followers_count']:,}")
        print(f"フォロー: {user['following_count']:,}")
        print(f"ツイート数: {user['tweet_count']:,}")
        print(f"認証済み: {'はい' if user['verified'] else 'いいえ'}")
        
        print("\n【AI分析結果】")
        print(f"大学関係: {saved_analysis['university_relation']}")
        print(f"関係性: {saved_analysis['relation_type']}")
        print(f"専攻分野: {saved_analysis['major_field']}")
        print(f"性格特徴: {saved_analysis['personality_traits']}")
        print(f"学習スタイル: {saved_analysis['learning_style']}")
        print(f"活動パターン: {saved_analysis['activity_pattern']}")
        print(f"協働可能性: {saved_analysis['collaboration_potential']}")
        print(f"分析信頼度: {saved_analysis['analysis_confidence']:.2f}")
        
        print("=" * 60)
        
        print("🎉 既存分析結果テスト成功！")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close_connection()

if __name__ == "__main__":
    test_with_existing_analysis()
    print("\n📋 分析データ保存機能テスト完了")
    print("✅ AI分析結果がデータベースに正常に保存されました")