#!/usr/bin/env python3
"""
興味・スキルリポジトリクラス
User_InterestsとUser_Skillsテーブルの操作を管理
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
import re
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
import logging
from database.database_manager import DatabaseManager, text_to_json

logger = logging.getLogger(__name__)

class InterestsSkillsRepository:
    """ユーザーの興味・スキル情報の永続化を管理するリポジトリクラス"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        興味・スキルリポジトリの初期化
        
        Args:
            db_manager: データベースマネージャーインスタンス
        """
        self.db = db_manager
    
    def extract_and_save_interests_skills(self, user_id: int, analysis_data: Dict[str, Any]) -> Tuple[int, int]:
        """
        AI分析結果から興味・スキルを抽出してデータベースに保存
        
        Args:
            user_id: ユーザーID
            analysis_data: AI分析結果
            
        Returns:
            (保存された興味数, 保存されたスキル数)
        """
        try:
            # 既存の興味・スキルを削除（最新データで更新）
            self._clear_user_interests_skills(user_id)
            
            # 分析データからJSONを抽出
            parsed_data = self._extract_json_from_analysis(analysis_data)
            
            # 興味を抽出・保存
            interests_count = self._save_interests(user_id, parsed_data)
            
            # スキルを抽出・保存
            skills_count = self._save_skills(user_id, parsed_data)
            
            logger.info(f"ユーザーID {user_id}: 興味 {interests_count}件, スキル {skills_count}件を保存")
            return interests_count, skills_count
            
        except Exception as e:
            logger.error(f"興味・スキル抽出エラー: {e}")
            raise
    
    def _extract_json_from_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析データからJSONを抽出"""
        analysis_text = analysis_data.get('analysis', '')
        
        # JSONブロックを検索
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', analysis_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # JSONブロックがない場合、テキストから抽出
        return self._extract_from_text(analysis_text)
    
    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """テキストから興味・スキル情報を抽出"""
        result = {
            'interests': [],
            'tech_skills': []
        }
        
        # 興味分野のキーワード検索
        interest_keywords = {
            'プログラミング': ['プログラミング', 'programming', 'コーディング'],
            'AI・機械学習': ['AI', '機械学習', 'ML', 'ディープラーニング', 'ChatGPT'],
            'Web開発': ['Web', 'HTML', 'CSS', 'JavaScript', 'React', 'Vue'],
            'データ分析': ['データ分析', 'データサイエンス', '統計', 'Python'],
            'IT・情報システム': ['IT', '情報システム', 'システム開発'],
            'メタバース': ['メタバース', 'VR', 'AR'],
            'ブログ': ['ブログ', 'blog', '執筆'],
            'スポーツ': ['野球', 'スポーツ', '運動'],
            '経済': ['経済', '投資', '金融']
        }
        
        for category, keywords in interest_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    result['interests'].append(category)
                    break
        
        # 技術スキルのキーワード検索
        skill_keywords = {
            'Python': ['Python', 'python'],
            'JavaScript': ['JavaScript', 'JS', 'React', 'Vue', 'Node'],
            'HTML/CSS': ['HTML', 'CSS'],
            'SQL': ['SQL', 'データベース'],
            'ChatGPT': ['ChatGPT', 'GPT'],
            'Git': ['Git', 'GitHub'],
            'Excel': ['Excel', 'スプレッドシート']
        }
        
        for skill, keywords in skill_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    result['tech_skills'].append(skill)
                    break
        
        return result
    
    def _save_interests(self, user_id: int, parsed_data: Dict[str, Any]) -> int:
        """興味データを保存"""
        interests = parsed_data.get('interests', [])
        if not isinstance(interests, list):
            interests = []
        
        count = 0
        for interest in interests:
            if isinstance(interest, str) and interest.strip():
                # カテゴリを判定
                category = self._categorize_interest(interest)
                
                # 信頼度を計算
                confidence = self._calculate_interest_confidence(interest, parsed_data)
                
                # データベースに保存
                query = """
                    INSERT INTO user_interests (
                        user_id, interest_category, interest_name, 
                        confidence_score, source
                    ) VALUES (?, ?, ?, ?, ?)
                """
                
                params = (user_id, category, interest, confidence, 'ai_analysis')
                self.db.execute_query(query, params)
                count += 1
        
        return count
    
    def _save_skills(self, user_id: int, parsed_data: Dict[str, Any]) -> int:
        """スキルデータを保存"""
        skills = parsed_data.get('tech_skills', [])
        if not isinstance(skills, list):
            skills = []
        
        count = 0
        for skill in skills:
            if isinstance(skill, str) and skill.strip():
                # カテゴリとレベルを判定
                category = self._categorize_skill(skill)
                level = self._estimate_skill_level(skill, parsed_data)
                
                # 信頼度を計算
                confidence = self._calculate_skill_confidence(skill, parsed_data)
                
                # データベースに保存
                query = """
                    INSERT INTO user_skills (
                        user_id, skill_name, skill_level, skill_category,
                        confidence_score, source
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """
                
                params = (user_id, skill, level, category, confidence, 'ai_analysis')
                self.db.execute_query(query, params)
                count += 1
        
        return count
    
    def _categorize_interest(self, interest: str) -> str:
        """興味のカテゴリを判定"""
        categories = {
            '技術': ['プログラミング', 'AI', 'Web', 'IT', 'システム', 'データ'],
            '学習': ['学習', '勉強', '授業', '課題'],
            '趣味': ['ブログ', 'スポーツ', '野球', 'ゲーム'],
            'ビジネス': ['経済', '投資', '経営', 'ビジネス'],
            'その他': []
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in interest:
                    return category
        
        return 'その他'
    
    def _categorize_skill(self, skill: str) -> str:
        """スキルのカテゴリを判定"""
        categories = {
            'プログラミング': ['Python', 'JavaScript', 'Java', 'C++', 'PHP'],
            'Web開発': ['HTML', 'CSS', 'React', 'Vue', 'Angular'],
            'データ分析': ['SQL', 'Excel', 'R', 'Tableau'],
            'AI・機械学習': ['ChatGPT', 'TensorFlow', 'PyTorch'],
            'ツール': ['Git', 'Docker', 'AWS'],
            'その他': []
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in skill:
                    return category
        
        return 'その他'
    
    def _estimate_skill_level(self, skill: str, parsed_data: Dict[str, Any]) -> str:
        """スキルレベルを推定"""
        # 学習スタイルや活動パターンから推定
        learning_style = parsed_data.get('learning_style', '')
        activity_pattern = parsed_data.get('activity_pattern', '')
        
        # 大学生なので基本的に初級〜中級
        if '上級' in learning_style or '経験豊富' in activity_pattern:
            return '中級'
        elif '学習中' in learning_style or '勉強' in activity_pattern:
            return '初級'
        else:
            return '初級'  # デフォルト
    
    def _calculate_interest_confidence(self, interest: str, parsed_data: Dict[str, Any]) -> float:
        """興味の信頼度を計算"""
        confidence = 0.5  # ベース信頼度
        
        # プロフィールに明記されている場合
        bio = parsed_data.get('bio', '')
        if interest in bio:
            confidence += 0.3
        
        # 複数の証拠がある場合
        if len(parsed_data.get('interests', [])) >= 3:
            confidence += 0.1
        
        # 大学関係が高い場合
        if parsed_data.get('university_relation') == '高':
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _calculate_skill_confidence(self, skill: str, parsed_data: Dict[str, Any]) -> float:
        """スキルの信頼度を計算"""
        confidence = 0.6  # ベース信頼度（興味より高め）
        
        # 専攻分野と関連がある場合
        major_field = parsed_data.get('major_field', '')
        if major_field == '情報学' and skill in ['Python', 'JavaScript', 'HTML', 'CSS']:
            confidence += 0.2
        
        # 学習スタイルに言及がある場合
        learning_style = parsed_data.get('learning_style', '')
        if skill.lower() in learning_style.lower():
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _clear_user_interests_skills(self, user_id: int):
        """ユーザーの既存興味・スキルを削除"""
        self.db.execute_query("DELETE FROM user_interests WHERE user_id = ?", (user_id,))
        self.db.execute_query("DELETE FROM user_skills WHERE user_id = ?", (user_id,))
    
    def get_user_interests(self, user_id: int) -> List[Dict[str, Any]]:
        """ユーザーの興味一覧を取得"""
        query = """
            SELECT * FROM user_interests 
            WHERE user_id = ? 
            ORDER BY confidence_score DESC, created_at DESC
        """
        return self.db.fetch_all(query, (user_id,))
    
    def get_user_skills(self, user_id: int) -> List[Dict[str, Any]]:
        """ユーザーのスキル一覧を取得"""
        query = """
            SELECT * FROM user_skills 
            WHERE user_id = ? 
            ORDER BY confidence_score DESC, created_at DESC
        """
        return self.db.fetch_all(query, (user_id,))
    
    def find_users_by_interest(self, interest_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """共通の興味を持つユーザーを検索"""
        query = """
            SELECT ui.*, u.twitter_username, u.name 
            FROM user_interests ui
            JOIN users u ON ui.user_id = u.id
            WHERE u.is_active = TRUE 
            AND ui.interest_name LIKE ?
            ORDER BY ui.confidence_score DESC
            LIMIT ?
        """
        return self.db.fetch_all(query, (f"%{interest_name}%", limit))
    
    def find_users_by_skill(self, skill_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """共通のスキルを持つユーザーを検索"""
        query = """
            SELECT us.*, u.twitter_username, u.name 
            FROM user_skills us
            JOIN users u ON us.user_id = u.id
            WHERE u.is_active = TRUE 
            AND us.skill_name LIKE ?
            ORDER BY us.confidence_score DESC
            LIMIT ?
        """
        return self.db.fetch_all(query, (f"%{skill_name}%", limit))
    
    def get_interest_statistics(self) -> Dict[str, Any]:
        """興味の統計情報を取得"""
        stats = {}
        
        # 人気の興味ランキング
        popular_interests_query = """
            SELECT interest_name, COUNT(*) as user_count, AVG(confidence_score) as avg_confidence
            FROM user_interests 
            GROUP BY interest_name 
            ORDER BY user_count DESC, avg_confidence DESC
            LIMIT 10
        """
        stats['popular_interests'] = self.db.fetch_all(popular_interests_query)
        
        # カテゴリ別分布
        category_query = """
            SELECT interest_category, COUNT(*) as count 
            FROM user_interests 
            GROUP BY interest_category 
            ORDER BY count DESC
        """
        stats['interest_categories'] = self.db.fetch_all(category_query)
        
        return stats
    
    def get_skill_statistics(self) -> Dict[str, Any]:
        """スキルの統計情報を取得"""
        stats = {}
        
        # 人気のスキルランキング
        popular_skills_query = """
            SELECT skill_name, COUNT(*) as user_count, AVG(confidence_score) as avg_confidence
            FROM user_skills 
            GROUP BY skill_name 
            ORDER BY user_count DESC, avg_confidence DESC
            LIMIT 10
        """
        stats['popular_skills'] = self.db.fetch_all(popular_skills_query)
        
        # スキルレベル分布
        level_query = """
            SELECT skill_level, COUNT(*) as count 
            FROM user_skills 
            GROUP BY skill_level 
            ORDER BY count DESC
        """
        stats['skill_levels'] = self.db.fetch_all(level_query)
        
        # カテゴリ別分布
        category_query = """
            SELECT skill_category, COUNT(*) as count 
            FROM user_skills 
            GROUP BY skill_category 
            ORDER BY count DESC
        """
        stats['skill_categories'] = self.db.fetch_all(category_query)
        
        return stats


if __name__ == "__main__":
    # テスト実行
    print("🧪 InterestsSkillsRepository テスト開始")
    
    # テスト用データベース
    db = DatabaseManager("test_interests_skills.db")
    repo = InterestsSkillsRepository(db)
    
    try:
        # テスト用分析データ
        test_analysis_data = {
            'analysis': '''```json
{
  "interests": ["プログラミング", "AI・機械学習", "Web開発", "データ分析"],
  "tech_skills": ["Python", "JavaScript", "HTML/CSS", "ChatGPT"],
  "major_field": "情報学",
  "learning_style": "オンライン学習に適応、実践的な学習を好む",
  "bio": "東京通信大学でプログラミングを学んでいます"
}
```'''
        }
        
        # 1. 興味・スキル抽出・保存テスト
        print("✅ 興味・スキル抽出・保存テスト")
        interests_count, skills_count = repo.extract_and_save_interests_skills(1, test_analysis_data)
        print(f"保存された興味: {interests_count}件, スキル: {skills_count}件")
        
        # 2. 興味・スキル取得テスト
        print("✅ 興味・スキル取得テスト")
        interests = repo.get_user_interests(1)
        skills = repo.get_user_skills(1)
        
        print("興味一覧:")
        for interest in interests:
            print(f"  - {interest['interest_name']} ({interest['interest_category']}) 信頼度: {interest['confidence_score']:.2f}")
        
        print("スキル一覧:")
        for skill in skills:
            print(f"  - {skill['skill_name']} ({skill['skill_category']}, {skill['skill_level']}) 信頼度: {skill['confidence_score']:.2f}")
        
        # 3. 統計テスト
        print("✅ 統計テスト")
        interest_stats = repo.get_interest_statistics()
        skill_stats = repo.get_skill_statistics()
        
        print("人気の興味:")
        for item in interest_stats['popular_interests']:
            print(f"  - {item['interest_name']}: {item['user_count']}人")
        
        print("人気のスキル:")
        for item in skill_stats['popular_skills']:
            print(f"  - {item['skill_name']}: {item['user_count']}人")
        
        print("🎉 InterestsSkillsRepository テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close_connection()
        # テストファイルを削除
        if os.path.exists("test_interests_skills.db"):
            os.remove("test_interests_skills.db")