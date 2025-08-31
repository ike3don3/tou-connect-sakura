#!/usr/bin/env python3
"""
マッチングエンジンクラス
学友の相性計算とマッチング推薦を管理
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import math
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import logging
from database.database_manager import DatabaseManager
from repositories.user_repository import UserRepository
from repositories.analysis_repository import AnalysisRepository
from repositories.interests_skills_repository import InterestsSkillsRepository

logger = logging.getLogger(__name__)

class MatchingEngine:
    """学友マッチングの相性計算エンジン"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        マッチングエンジンの初期化
        
        Args:
            db_manager: データベースマネージャーインスタンス
        """
        self.db = db_manager
        self.user_repo = UserRepository(db_manager)
        self.analysis_repo = AnalysisRepository(db_manager)
        self.interests_skills_repo = InterestsSkillsRepository(db_manager)
    
    def calculate_compatibility(self, user1_id: int, user2_id: int) -> float:
        """
        2人のユーザー間の相性スコアを計算
        
        Args:
            user1_id: ユーザー1のID
            user2_id: ユーザー2のID
            
        Returns:
            相性スコア（0.0-1.0）
        """
        try:
            # ユーザー情報を取得
            user1_data = self._get_user_complete_data(user1_id)
            user2_data = self._get_user_complete_data(user2_id)
            
            if not user1_data or not user2_data:
                logger.warning(f"ユーザーデータが不完全: {user1_id}, {user2_id}")
                return 0.0
            
            # 各要素の相性を計算
            scores = {
                'interests': self._calculate_interest_compatibility(user1_data, user2_data),
                'skills': self._calculate_skill_compatibility(user1_data, user2_data),
                'major_field': self._calculate_major_field_compatibility(user1_data, user2_data),
                'learning_style': self._calculate_learning_style_compatibility(user1_data, user2_data),
                'personality': self._calculate_personality_compatibility(user1_data, user2_data),
                'university_relation': self._calculate_university_relation_compatibility(user1_data, user2_data),
                'location': self._calculate_location_compatibility(user1_data, user2_data),
                'activity_level': self._calculate_activity_level_compatibility(user1_data, user2_data)
            }
            
            # 重み付き平均で総合スコアを計算
            weights = {
                'interests': 0.25,      # 共通興味（最重要）
                'skills': 0.20,         # 技術スキル
                'major_field': 0.15,    # 専攻分野
                'learning_style': 0.10, # 学習スタイル
                'personality': 0.10,    # 性格相性
                'university_relation': 0.10, # 大学関係
                'location': 0.05,       # 地理的近さ
                'activity_level': 0.05  # 活動レベル
            }
            
            total_score = sum(scores[key] * weights[key] for key in scores.keys())
            
            logger.info(f"相性計算完了: ユーザー{user1_id} - ユーザー{user2_id} = {total_score:.3f}")
            logger.debug(f"詳細スコア: {scores}")
            
            return min(max(total_score, 0.0), 1.0)  # 0.0-1.0の範囲に制限
            
        except Exception as e:
            logger.error(f"相性計算エラー: {e}")
            return 0.0
    
    def _get_user_complete_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """ユーザーの完全なデータを取得"""
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            return None
        
        analysis = self.analysis_repo.get_latest_analysis(user_id)
        interests = self.interests_skills_repo.get_user_interests(user_id)
        skills = self.interests_skills_repo.get_user_skills(user_id)
        
        return {
            'user': user,
            'analysis': analysis,
            'interests': interests,
            'skills': skills
        }
    
    def _calculate_interest_compatibility(self, user1_data: Dict, user2_data: Dict) -> float:
        """興味の相性を計算"""
        interests1 = {item['interest_name'].lower() for item in user1_data['interests']}
        interests2 = {item['interest_name'].lower() for item in user2_data['interests']}
        
        if not interests1 or not interests2:
            return 0.0
        
        # Jaccard係数を計算
        intersection = len(interests1.intersection(interests2))
        union = len(interests1.union(interests2))
        
        if union == 0:
            return 0.0
        
        jaccard_score = intersection / union
        
        # 共通興味の重要度を考慮
        common_interests = interests1.intersection(interests2)
        importance_bonus = 0.0
        
        # 技術系の共通興味にボーナス
        tech_interests = {'プログラミング', 'ai・機械学習', 'web開発', 'データ分析', 'it・情報システム'}
        tech_common = len([i for i in common_interests if i in tech_interests])
        importance_bonus += tech_common * 0.1
        
        return min(jaccard_score + importance_bonus, 1.0)
    
    def _calculate_skill_compatibility(self, user1_data: Dict, user2_data: Dict) -> float:
        """スキルの相性を計算"""
        skills1 = {item['skill_name'].lower() for item in user1_data['skills']}
        skills2 = {item['skill_name'].lower() for item in user2_data['skills']}
        
        if not skills1 or not skills2:
            return 0.0
        
        # 共通スキルと補完スキルを評価
        common_skills = skills1.intersection(skills2)
        
        # 共通スキルスコア
        common_score = len(common_skills) / max(len(skills1), len(skills2))
        
        # 補完スキルスコア（異なるが関連するスキル）
        complement_score = self._calculate_skill_complement(skills1, skills2)
        
        # 重み付き平均
        return (common_score * 0.7) + (complement_score * 0.3)
    
    def _calculate_skill_complement(self, skills1: set, skills2: set) -> float:
        """スキルの補完性を計算"""
        # 関連スキルのマッピング
        skill_groups = {
            'web_frontend': {'javascript', 'html/css', 'react', 'vue'},
            'web_backend': {'python', 'java', 'php', 'node.js'},
            'data_science': {'python', 'sql', 'excel', 'r'},
            'ai_ml': {'python', 'chatgpt', 'tensorflow', 'pytorch'}
        }
        
        complement_score = 0.0
        
        for group_name, group_skills in skill_groups.items():
            skills1_in_group = skills1.intersection(group_skills)
            skills2_in_group = skills2.intersection(group_skills)
            
            # 同じグループ内で異なるスキルを持つ場合、補完性あり
            if skills1_in_group and skills2_in_group and skills1_in_group != skills2_in_group:
                complement_score += 0.2
        
        return min(complement_score, 1.0)
    
    def _calculate_major_field_compatibility(self, user1_data: Dict, user2_data: Dict) -> float:
        """専攻分野の相性を計算"""
        if not user1_data['analysis'] or not user2_data['analysis']:
            return 0.0
        
        major1 = user1_data['analysis']['major_field']
        major2 = user2_data['analysis']['major_field']
        
        if major1 == major2:
            return 1.0
        
        # 関連分野の相性
        related_fields = {
            '情報学': ['経営学'],
            '経営学': ['情報学'],
        }
        
        if major1 in related_fields and major2 in related_fields[major1]:
            return 0.7
        
        return 0.3  # 異なる分野でも基本的な相性
    
    def _calculate_learning_style_compatibility(self, user1_data: Dict, user2_data: Dict) -> float:
        """学習スタイルの相性を計算"""
        if not user1_data['analysis'] or not user2_data['analysis']:
            return 0.5
        
        style1 = user1_data['analysis']['learning_style'].lower()
        style2 = user2_data['analysis']['learning_style'].lower()
        
        # キーワードベースの相性判定
        compatible_keywords = [
            (['オンライン', 'online'], ['オンライン', 'online']),
            (['実践', '実習'], ['実践', '実習']),
            (['理論', '概念'], ['理論', '概念']),
            (['グループ', '協力'], ['グループ', '協力']),
            (['個人', '自主'], ['個人', '自主'])
        ]
        
        compatibility_score = 0.5  # ベーススコア
        
        for keywords1, keywords2 in compatible_keywords:
            has_style1 = any(kw in style1 for kw in keywords1)
            has_style2 = any(kw in style2 for kw in keywords2)
            
            if has_style1 and has_style2:
                compatibility_score += 0.1
        
        return min(compatibility_score, 1.0)
    
    def _calculate_personality_compatibility(self, user1_data: Dict, user2_data: Dict) -> float:
        """性格の相性を計算"""
        if not user1_data['analysis'] or not user2_data['analysis']:
            return 0.5
        
        traits1 = user1_data['analysis']['personality_traits'].lower()
        traits2 = user2_data['analysis']['personality_traits'].lower()
        
        # 相性の良い性格の組み合わせ
        compatible_pairs = [
            (['論理的', '分析的'], ['論理的', '分析的']),
            (['創造的', 'クリエイティブ'], ['創造的', 'クリエイティブ']),
            (['協調的', '社交的'], ['協調的', '社交的']),
            (['効率的', '計画的'], ['効率的', '計画的'])
        ]
        
        compatibility_score = 0.5
        
        for traits_set1, traits_set2 in compatible_pairs:
            has_trait1 = any(trait in traits1 for trait in traits_set1)
            has_trait2 = any(trait in traits2 for trait in traits_set2)
            
            if has_trait1 and has_trait2:
                compatibility_score += 0.125
        
        return min(compatibility_score, 1.0)
    
    def _calculate_university_relation_compatibility(self, user1_data: Dict, user2_data: Dict) -> float:
        """大学関係の相性を計算"""
        if not user1_data['analysis'] or not user2_data['analysis']:
            return 0.0
        
        relation1 = user1_data['analysis']['university_relation']
        relation2 = user2_data['analysis']['university_relation']
        
        # 両方とも大学関係者の場合、高い相性
        if relation1 == '高' and relation2 == '高':
            return 1.0
        elif (relation1 == '高' and relation2 == '中') or (relation1 == '中' and relation2 == '高'):
            return 0.8
        elif relation1 == '中' and relation2 == '中':
            return 0.6
        else:
            return 0.3
    
    def _calculate_location_compatibility(self, user1_data: Dict, user2_data: Dict) -> float:
        """地理的な相性を計算"""
        location1 = user1_data['user']['location'] or ''
        location2 = user2_data['user']['location'] or ''
        
        if not location1 or not location2:
            return 0.5  # 不明な場合は中立
        
        location1 = location1.lower()
        location2 = location2.lower()
        
        # 都道府県レベルでの一致
        prefectures = ['東京', '神奈川', '千葉', '埼玉', '大阪', '京都', '兵庫']
        
        for pref in prefectures:
            if pref in location1 and pref in location2:
                return 1.0
        
        # 関東圏内での相性
        kanto = ['東京', '神奈川', '千葉', '埼玉', '茨城', '栃木', '群馬']
        in_kanto1 = any(pref in location1 for pref in kanto)
        in_kanto2 = any(pref in location2 for pref in kanto)
        
        if in_kanto1 and in_kanto2:
            return 0.8
        
        return 0.3
    
    def _calculate_activity_level_compatibility(self, user1_data: Dict, user2_data: Dict) -> float:
        """活動レベルの相性を計算"""
        followers1 = user1_data['user']['followers_count']
        followers2 = user2_data['user']['followers_count']
        tweets1 = user1_data['user']['tweet_count']
        tweets2 = user2_data['user']['tweet_count']
        
        # 活動レベルを正規化（0-1）
        def normalize_activity(followers, tweets):
            # フォロワー数とツイート数から活動レベルを計算
            follower_score = min(followers / 1000, 1.0)  # 1000フォロワーで最大
            tweet_score = min(tweets / 5000, 1.0)        # 5000ツイートで最大
            return (follower_score + tweet_score) / 2
        
        activity1 = normalize_activity(followers1, tweets1)
        activity2 = normalize_activity(followers2, tweets2)
        
        # 活動レベルの差が小さいほど相性が良い
        activity_diff = abs(activity1 - activity2)
        return 1.0 - activity_diff
    
    def find_potential_matches(self, user_id: int, limit: int = 10, min_score: float = 0.3) -> List[Dict[str, Any]]:
        """
        ユーザーの潜在的なマッチを検索
        
        Args:
            user_id: 対象ユーザーのID
            limit: 返す最大件数
            min_score: 最小相性スコア
            
        Returns:
            マッチ候補のリスト（相性スコア順）
        """
        try:
            # 全ユーザーを取得（自分以外）
            all_users = self.user_repo.search_users({})
            candidate_users = [u for u in all_users if u['id'] != user_id]
            
            matches = []
            
            for candidate in candidate_users:
                # 相性スコアを計算
                compatibility_score = self.calculate_compatibility(user_id, candidate['id'])
                
                if compatibility_score >= min_score:
                    # マッチ理由を生成
                    match_reasons = self.generate_match_reasons(user_id, candidate['id'])
                    
                    matches.append({
                        'user_id': candidate['id'],
                        'username': candidate['twitter_username'],
                        'name': candidate['name'],
                        'compatibility_score': compatibility_score,
                        'match_reasons': match_reasons
                    })
            
            # 相性スコア順でソート
            matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
            
            logger.info(f"ユーザー{user_id}のマッチ候補: {len(matches)}件（上位{limit}件を返却）")
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"マッチ検索エラー: {e}")
            return []
    
    def generate_match_reasons(self, user1_id: int, user2_id: int) -> List[str]:
        """
        マッチ理由を生成
        
        Args:
            user1_id: ユーザー1のID
            user2_id: ユーザー2のID
            
        Returns:
            マッチ理由のリスト
        """
        try:
            user1_data = self._get_user_complete_data(user1_id)
            user2_data = self._get_user_complete_data(user2_id)
            
            if not user1_data or not user2_data:
                return ["データが不完全です"]
            
            reasons = []
            
            # 共通興味
            interests1 = {item['interest_name'] for item in user1_data['interests']}
            interests2 = {item['interest_name'] for item in user2_data['interests']}
            common_interests = interests1.intersection(interests2)
            
            if common_interests:
                reasons.append(f"共通の興味: {', '.join(list(common_interests)[:3])}")
            
            # 共通スキル
            skills1 = {item['skill_name'] for item in user1_data['skills']}
            skills2 = {item['skill_name'] for item in user2_data['skills']}
            common_skills = skills1.intersection(skills2)
            
            if common_skills:
                reasons.append(f"共通のスキル: {', '.join(list(common_skills)[:3])}")
            
            # 同じ専攻
            if (user1_data['analysis'] and user2_data['analysis'] and 
                user1_data['analysis']['major_field'] == user2_data['analysis']['major_field']):
                reasons.append(f"同じ専攻: {user1_data['analysis']['major_field']}")
            
            # 同じ地域
            location1 = user1_data['user']['location'] or ''
            location2 = user2_data['user']['location'] or ''
            
            if location1 and location2:
                for pref in ['東京', '神奈川', '千葉', '埼玉']:
                    if pref in location1 and pref in location2:
                        reasons.append(f"同じ地域: {pref}")
                        break
            
            # 大学関係
            if (user1_data['analysis'] and user2_data['analysis'] and
                user1_data['analysis']['university_relation'] == '高' and
                user2_data['analysis']['university_relation'] == '高'):
                reasons.append("東京通信大学の関係者")
            
            return reasons if reasons else ["学習パートナーとしての可能性"]
            
        except Exception as e:
            logger.error(f"マッチ理由生成エラー: {e}")
            return ["分析中にエラーが発生しました"]


if __name__ == "__main__":
    # テスト実行
    print("🧪 MatchingEngine テスト開始")
    
    # テスト用データベース
    db = DatabaseManager("test_matching.db")
    matching_engine = MatchingEngine(db)
    
    try:
        # テスト用ユーザーデータを作成
        user_repo = UserRepository(db)
        analysis_repo = AnalysisRepository(db)
        interests_repo = InterestsSkillsRepository(db)
        
        # ユーザー1を作成
        user1_data = {
            'username': 'test_user1',
            'id': 'test_id_1',
            'name': 'テストユーザー1',
            'description': '東京通信大学でプログラミングを学んでいます',
            'location': '東京都',
            'followers_count': 100,
            'following_count': 150,
            'tweet_count': 500
        }
        user1_id = user_repo.create_user(user1_data)
        
        # ユーザー2を作成
        user2_data = {
            'username': 'test_user2',
            'id': 'test_id_2',
            'name': 'テストユーザー2',
            'description': '東京通信大学でAIを学んでいます',
            'location': '神奈川県',
            'followers_count': 200,
            'following_count': 180,
            'tweet_count': 800
        }
        user2_id = user_repo.create_user(user2_data)
        
        # 分析データを作成
        analysis1 = {
            'analysis': '{"university_relation": "高", "major_field": "情報学", "interests": ["プログラミング", "Web開発"], "tech_skills": ["Python", "JavaScript"]}'
        }
        analysis_repo.save_analysis(user1_id, analysis1)
        interests_repo.extract_and_save_interests_skills(user1_id, analysis1)
        
        analysis2 = {
            'analysis': '{"university_relation": "高", "major_field": "情報学", "interests": ["AI・機械学習", "プログラミング"], "tech_skills": ["Python", "ChatGPT"]}'
        }
        analysis_repo.save_analysis(user2_id, analysis2)
        interests_repo.extract_and_save_interests_skills(user2_id, analysis2)
        
        # 1. 相性計算テスト
        print("✅ 相性計算テスト")
        compatibility = matching_engine.calculate_compatibility(user1_id, user2_id)
        print(f"相性スコア: {compatibility:.3f}")
        
        # 2. マッチ理由生成テスト
        print("✅ マッチ理由生成テスト")
        reasons = matching_engine.generate_match_reasons(user1_id, user2_id)
        print("マッチ理由:")
        for reason in reasons:
            print(f"  - {reason}")
        
        # 3. マッチ検索テスト
        print("✅ マッチ検索テスト")
        matches = matching_engine.find_potential_matches(user1_id)
        print(f"マッチ候補: {len(matches)}件")
        
        for match in matches:
            print(f"  - {match['name']} (@{match['username']})")
            print(f"    相性: {match['compatibility_score']:.3f}")
            print(f"    理由: {', '.join(match['match_reasons'])}")
        
        print("🎉 MatchingEngine テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close_connection()
        # テストファイルを削除
        if os.path.exists("test_matching.db"):
            os.remove("test_matching.db")