#!/usr/bin/env python3
"""
学習リソース推薦エンジン
ユーザーの興味・スキルに基づいて学習リソースを推薦
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from typing import Dict, List, Any
import logging
from database.database_manager import DatabaseManager
from repositories.interests_skills_repository import InterestsSkillsRepository

logger = logging.getLogger(__name__)

class LearningResourceRecommender:
    """学習リソース推薦エンジン"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.interests_skills_repo = InterestsSkillsRepository(db_manager)
        
        # 学習リソースデータベース（実際にはAPIから取得）
        self.resources = {
            'プログラミング': [
                {
                    'title': 'Python実践入門',
                    'type': 'book',
                    'price': 3200,
                    'affiliate_url': 'https://amzn.to/python-book',
                    'description': 'Pythonの基礎から実践まで学べる決定版',
                    'rating': 4.5,
                    'level': '初級-中級'
                },
                {
                    'title': 'Python完全攻略コース',
                    'type': 'course',
                    'price': 12000,
                    'affiliate_url': 'https://udemy.com/python-course',
                    'description': '100時間でPythonマスター',
                    'rating': 4.7,
                    'level': '初級-上級'
                }
            ],
            'AI・機械学習': [
                {
                    'title': 'ゼロから作るDeep Learning',
                    'type': 'book',
                    'price': 3740,
                    'affiliate_url': 'https://amzn.to/deep-learning',
                    'description': 'ディープラーニングの理論と実装',
                    'rating': 4.6,
                    'level': '中級-上級'
                },
                {
                    'title': '機械学習実践コース',
                    'type': 'course',
                    'price': 15000,
                    'affiliate_url': 'https://udemy.com/ml-course',
                    'description': 'scikit-learnで学ぶ機械学習',
                    'rating': 4.4,
                    'level': '中級'
                }
            ],
            'Web開発': [
                {
                    'title': 'React実践の教科書',
                    'type': 'book',
                    'price': 3520,
                    'affiliate_url': 'https://amzn.to/react-book',
                    'description': 'モダンReact開発の決定版',
                    'rating': 4.3,
                    'level': '中級'
                },
                {
                    'title': 'フルスタックWeb開発',
                    'type': 'course',
                    'price': 18000,
                    'affiliate_url': 'https://udemy.com/fullstack-course',
                    'description': 'React + Node.js完全マスター',
                    'rating': 4.5,
                    'level': '中級-上級'
                }
            ],
            'データ分析': [
                {
                    'title': 'Pythonによるデータ分析入門',
                    'type': 'book',
                    'price': 4180,
                    'affiliate_url': 'https://amzn.to/data-analysis',
                    'description': 'pandas、NumPyでデータ分析',
                    'rating': 4.4,
                    'level': '初級-中級'
                },
                {
                    'title': 'データサイエンス実践',
                    'type': 'course',
                    'price': 14000,
                    'affiliate_url': 'https://udemy.com/data-science',
                    'description': 'ビジネスデータ分析の実践',
                    'rating': 4.6,
                    'level': '中級'
                }
            ]
        }
    
    def get_recommendations(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        ユーザーに最適な学習リソースを推薦
        
        Args:
            user_id: ユーザーID
            limit: 推薦する最大件数
            
        Returns:
            推薦リソースのリスト
        """
        try:
            # ユーザーの興味・スキルを取得
            interests = self.interests_skills_repo.get_user_interests(user_id)
            skills = self.interests_skills_repo.get_user_skills(user_id)
            
            recommendations = []
            
            # 興味に基づく推薦
            for interest in interests:
                interest_name = interest['interest_name']
                if interest_name in self.resources:
                    for resource in self.resources[interest_name]:
                        # スキルレベルに基づくフィルタリング
                        if self._is_suitable_level(resource, skills):
                            resource_with_score = resource.copy()
                            resource_with_score['relevance_score'] = self._calculate_relevance(
                                resource, interest, skills
                            )
                            resource_with_score['interest_match'] = interest_name
                            recommendations.append(resource_with_score)
            
            # 関連性スコア順でソート
            recommendations.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # 重複除去
            seen_titles = set()
            unique_recommendations = []
            for rec in recommendations:
                if rec['title'] not in seen_titles:
                    seen_titles.add(rec['title'])
                    unique_recommendations.append(rec)
            
            logger.info(f"ユーザー{user_id}に{len(unique_recommendations[:limit])}件の学習リソースを推薦")
            return unique_recommendations[:limit]
            
        except Exception as e:
            logger.error(f"学習リソース推薦エラー: {e}")
            return []
    
    def _is_suitable_level(self, resource: Dict, user_skills: List[Dict]) -> bool:
        """リソースがユーザーのスキルレベルに適しているかチェック"""
        resource_level = resource.get('level', '初級')
        
        # ユーザーのスキルレベルを判定
        user_level = '初級'  # デフォルト
        
        for skill in user_skills:
            if skill['skill_level'] in ['中級', '上級']:
                user_level = skill['skill_level']
                break
        
        # レベル適合性チェック
        if user_level == '初級':
            return '初級' in resource_level
        elif user_level == '中級':
            return '中級' in resource_level or '初級' in resource_level
        else:  # 上級
            return True  # 上級者はすべてのレベルに対応
    
    def _calculate_relevance(self, resource: Dict, interest: Dict, skills: List[Dict]) -> float:
        """関連性スコアを計算"""
        score = 0.0
        
        # 基本スコア（興味の信頼度）
        score += interest['confidence_score'] * 0.4
        
        # 評価スコア
        score += (resource['rating'] / 5.0) * 0.3
        
        # スキル関連性
        resource_title = resource['title'].lower()
        for skill in skills:
            if skill['skill_name'].lower() in resource_title:
                score += skill['confidence_score'] * 0.2
        
        # タイプボーナス（実践的なコースを優遇）
        if resource['type'] == 'course':
            score += 0.1
        
        return min(score, 1.0)
    
    def get_popular_resources(self, category: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """人気の学習リソースを取得"""
        all_resources = []
        
        categories = [category] if category else self.resources.keys()
        
        for cat in categories:
            if cat in self.resources:
                for resource in self.resources[cat]:
                    resource_with_cat = resource.copy()
                    resource_with_cat['category'] = cat
                    all_resources.append(resource_with_cat)
        
        # 評価順でソート
        all_resources.sort(key=lambda x: x['rating'], reverse=True)
        
        return all_resources[:limit]
    
    def track_click(self, user_id: int, resource_title: str, affiliate_url: str):
        """アフィリエイトクリックを追跡"""
        try:
            # クリック追跡をデータベースに記録
            query = """
                INSERT INTO affiliate_clicks (user_id, resource_title, affiliate_url, clicked_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """
            # 実際の実装では専用テーブルを作成
            logger.info(f"アフィリエイトクリック追跡: ユーザー{user_id} -> {resource_title}")
            
        except Exception as e:
            logger.error(f"クリック追跡エラー: {e}")


if __name__ == "__main__":
    # テスト実行
    print("📚 学習リソース推薦エンジンテスト開始")
    
    db = DatabaseManager("tou_connect.db")
    recommender = LearningResourceRecommender(db)
    
    try:
        # ユーザー1（@ike3don3）への推薦テスト
        print("✅ 個別推薦テスト")
        recommendations = recommender.get_recommendations(1, limit=3)
        
        print(f"推薦リソース: {len(recommendations)}件")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['title']} ({rec['type']})")
            print(f"   価格: ¥{rec['price']:,}")
            print(f"   評価: {rec['rating']}/5.0")
            print(f"   レベル: {rec['level']}")
            print(f"   関連性: {rec['relevance_score']:.2f}")
            print(f"   マッチした興味: {rec['interest_match']}")
        
        # 人気リソーステスト
        print("\n✅ 人気リソーステスト")
        popular = recommender.get_popular_resources(limit=3)
        
        print(f"人気リソース: {len(popular)}件")
        for i, res in enumerate(popular, 1):
            print(f"{i}. {res['title']} - {res['category']} (評価: {res['rating']})")
        
        print("🎉 学習リソース推薦エンジンテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close_connection()