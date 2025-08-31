#!/usr/bin/env python3
"""
分析結果リポジトリクラス
User_Analysisテーブルの操作を管理
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
import re
from datetime import datetime
from typing import Optional, Dict, List, Any
import logging
from database.database_manager import DatabaseManager, AnalysisError, json_to_text, text_to_json

logger = logging.getLogger(__name__)

class AnalysisRepository:
    """AI分析結果の永続化を管理するリポジトリクラス"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        分析リポジトリの初期化
        
        Args:
            db_manager: データベースマネージャーインスタンス
        """
        self.db = db_manager
    
    def save_analysis(self, user_id: int, analysis_data: Dict[str, Any]) -> int:
        """
        AI分析結果を保存
        
        Args:
            user_id: 対象ユーザーのID
            analysis_data: Gemini APIからの分析結果
            
        Returns:
            保存された分析レコードのID
        """
        try:
            # 既存の分析結果を確認
            existing_analysis = self.get_latest_analysis(user_id)
            
            # 分析データを解析・構造化
            structured_data = self._parse_analysis_data(analysis_data)
            
            if existing_analysis:
                # 既存データを更新
                return self._update_analysis(existing_analysis['id'], structured_data)
            else:
                # 新規作成
                return self._create_analysis(user_id, structured_data)
                
        except Exception as e:
            logger.error(f"分析データ保存エラー: {e}")
            raise AnalysisError(f"分析データの保存に失敗: {e}")
    
    def _parse_analysis_data(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gemini APIの分析結果を構造化データに変換
        
        Args:
            analysis_data: 生の分析データ
            
        Returns:
            構造化された分析データ
        """
        try:
            # 分析テキストからJSONを抽出
            analysis_text = analysis_data.get('analysis', '')
            
            # JSONブロックを検索
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', analysis_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed_json = json.loads(json_str)
            else:
                # JSONブロックがない場合、テキスト全体をJSONとして解析を試行
                try:
                    parsed_json = json.loads(analysis_text)
                except json.JSONDecodeError:
                    # JSONとして解析できない場合、デフォルト構造を作成
                    parsed_json = self._extract_from_text(analysis_text)
            
            # 構造化データを作成
            structured = {
                'university_relation': parsed_json.get('university_relation', '不明'),
                'relation_type': parsed_json.get('relation_type', 'その他'),
                'major_field': parsed_json.get('major_field', '不明'),
                'personality_traits': json_to_text(parsed_json.get('personality_traits', [])),
                'learning_style': parsed_json.get('learning_style', ''),
                'activity_pattern': parsed_json.get('activity_pattern', ''),
                'collaboration_potential': parsed_json.get('collaboration_potential', '不明'),
                'analysis_confidence': self._calculate_confidence(parsed_json),
                'raw_analysis_data': json_to_text(analysis_data)
            }
            
            logger.info(f"分析データを構造化: {structured['university_relation']}, {structured['major_field']}")
            return structured
            
        except Exception as e:
            logger.error(f"分析データ解析エラー: {e}")
            # エラー時はデフォルト構造を返す
            return {
                'university_relation': '不明',
                'relation_type': 'その他',
                'major_field': '不明',
                'personality_traits': '',
                'learning_style': '',
                'activity_pattern': '',
                'collaboration_potential': '不明',
                'analysis_confidence': 0.0,
                'raw_analysis_data': json_to_text(analysis_data)
            }
    
    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """
        テキストから分析情報を抽出（JSONが利用できない場合）
        
        Args:
            text: 分析テキスト
            
        Returns:
            抽出された情報の辞書
        """
        result = {}
        
        # 大学関係の判定
        if '東京通信大学' in text or 'TOU' in text:
            result['university_relation'] = '高'
        elif '大学' in text:
            result['university_relation'] = '中'
        else:
            result['university_relation'] = '低'
        
        # 関係性の判定
        if '学生' in text:
            result['relation_type'] = '学生'
        elif '教員' in text or '先生' in text:
            result['relation_type'] = '教員'
        else:
            result['relation_type'] = 'その他'
        
        # 専攻分野の判定
        if 'プログラミング' in text or 'IT' in text or '情報' in text:
            result['major_field'] = '情報学'
        elif '経営' in text or 'ビジネス' in text:
            result['major_field'] = '経営学'
        else:
            result['major_field'] = 'その他'
        
        return result
    
    def _calculate_confidence(self, parsed_data: Dict[str, Any]) -> float:
        """
        分析結果の信頼度を計算
        
        Args:
            parsed_data: 解析済みデータ
            
        Returns:
            信頼度スコア（0.0-1.0）
        """
        confidence = 0.0
        
        # 大学関係の明確さ
        if parsed_data.get('university_relation') == '高':
            confidence += 0.3
        elif parsed_data.get('university_relation') == '中':
            confidence += 0.2
        
        # 専攻分野の特定度
        if parsed_data.get('major_field') not in ['不明', 'その他']:
            confidence += 0.2
        
        # 興味分野の数
        interests = parsed_data.get('interests', [])
        if isinstance(interests, list) and len(interests) >= 3:
            confidence += 0.2
        
        # 技術スキルの特定
        tech_skills = parsed_data.get('tech_skills', [])
        if isinstance(tech_skills, list) and len(tech_skills) >= 2:
            confidence += 0.2
        
        # 性格特徴の詳細度
        personality = parsed_data.get('personality_traits', [])
        if isinstance(personality, list) and len(personality) >= 2:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _create_analysis(self, user_id: int, structured_data: Dict[str, Any]) -> int:
        """新規分析レコードを作成"""
        query = """
            INSERT INTO user_analysis (
                user_id, university_relation, relation_type, major_field,
                personality_traits, learning_style, activity_pattern,
                collaboration_potential, analysis_confidence, raw_analysis_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            user_id,
            structured_data['university_relation'],
            structured_data['relation_type'],
            structured_data['major_field'],
            structured_data['personality_traits'],
            structured_data['learning_style'],
            structured_data['activity_pattern'],
            structured_data['collaboration_potential'],
            structured_data['analysis_confidence'],
            structured_data['raw_analysis_data']
        )
        
        cursor = self.db.execute_query(query, params)
        analysis_id = cursor.lastrowid
        
        logger.info(f"新規分析レコード作成: ユーザーID {user_id} → 分析ID {analysis_id}")
        return analysis_id
    
    def _update_analysis(self, analysis_id: int, structured_data: Dict[str, Any]) -> int:
        """既存分析レコードを更新"""
        query = """
            UPDATE user_analysis SET
                university_relation = ?, relation_type = ?, major_field = ?,
                personality_traits = ?, learning_style = ?, activity_pattern = ?,
                collaboration_potential = ?, analysis_confidence = ?, raw_analysis_data = ?,
                created_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        
        params = (
            structured_data['university_relation'],
            structured_data['relation_type'],
            structured_data['major_field'],
            structured_data['personality_traits'],
            structured_data['learning_style'],
            structured_data['activity_pattern'],
            structured_data['collaboration_potential'],
            structured_data['analysis_confidence'],
            structured_data['raw_analysis_data'],
            analysis_id
        )
        
        self.db.execute_query(query, params)
        logger.info(f"分析レコード更新: 分析ID {analysis_id}")
        return analysis_id
    
    def get_latest_analysis(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        ユーザーの最新分析結果を取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            最新の分析結果またはNone
        """
        query = """
            SELECT * FROM user_analysis 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        """
        return self.db.fetch_one(query, (user_id,))
    
    def get_analysis_by_id(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """
        分析IDで分析結果を取得
        
        Args:
            analysis_id: 分析ID
            
        Returns:
            分析結果またはNone
        """
        query = "SELECT * FROM user_analysis WHERE id = ?"
        return self.db.fetch_one(query, (analysis_id,))
    
    def get_users_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        分析結果の条件でユーザーを検索
        
        Args:
            criteria: 検索条件
            
        Returns:
            条件に合致するユーザーの分析結果リスト
        """
        query = """
            SELECT ua.*, u.twitter_username, u.name 
            FROM user_analysis ua
            JOIN users u ON ua.user_id = u.id
            WHERE u.is_active = TRUE
        """
        params = []
        
        # 検索条件を追加
        if criteria.get('university_relation'):
            query += " AND ua.university_relation = ?"
            params.append(criteria['university_relation'])
        
        if criteria.get('major_field'):
            query += " AND ua.major_field = ?"
            params.append(criteria['major_field'])
        
        if criteria.get('relation_type'):
            query += " AND ua.relation_type = ?"
            params.append(criteria['relation_type'])
        
        if criteria.get('min_confidence'):
            query += " AND ua.analysis_confidence >= ?"
            params.append(criteria['min_confidence'])
        
        query += " ORDER BY ua.created_at DESC"
        
        return self.db.fetch_all(query, tuple(params))
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """
        分析結果の統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        stats = {}
        
        # 総分析数
        total_result = self.db.fetch_one("SELECT COUNT(*) as count FROM user_analysis")
        stats['total_analyses'] = total_result['count'] if total_result else 0
        
        # 大学関係者の分布
        relation_query = """
            SELECT university_relation, COUNT(*) as count 
            FROM user_analysis 
            GROUP BY university_relation
        """
        stats['university_relation_distribution'] = self.db.fetch_all(relation_query)
        
        # 専攻分野の分布
        major_query = """
            SELECT major_field, COUNT(*) as count 
            FROM user_analysis 
            GROUP BY major_field 
            ORDER BY count DESC
        """
        stats['major_field_distribution'] = self.db.fetch_all(major_query)
        
        # 平均信頼度
        confidence_result = self.db.fetch_one("SELECT AVG(analysis_confidence) as avg_confidence FROM user_analysis")
        stats['average_confidence'] = confidence_result['avg_confidence'] if confidence_result else 0.0
        
        return stats


if __name__ == "__main__":
    # テスト実行
    print("🧪 AnalysisRepository テスト開始")
    
    # テスト用データベース
    db = DatabaseManager("test_analysis_repo.db")
    analysis_repo = AnalysisRepository(db)
    
    try:
        # テスト用分析データ
        test_analysis_data = {
            'username': 'test_user',
            'analysis': '''```json
{
  "university_relation": "高",
  "relation_type": "学生",
  "interests": ["プログラミング", "AI", "機械学習"],
  "major_field": "情報学",
  "personality_traits": ["論理的", "効率的"],
  "learning_style": "オンライン学習に適応",
  "activity_pattern": "継続的な学習",
  "tech_skills": ["Python", "JavaScript"],
  "collaboration_potential": "高"
}
```'''
        }
        
        # 1. 分析データ保存テスト
        print("✅ 分析データ保存テスト")
        analysis_id = analysis_repo.save_analysis(1, test_analysis_data)
        print(f"保存された分析ID: {analysis_id}")
        
        # 2. 分析データ取得テスト
        print("✅ 分析データ取得テスト")
        analysis = analysis_repo.get_latest_analysis(1)
        print(f"取得した分析: {analysis['university_relation']}, {analysis['major_field']}")
        
        # 3. 条件検索テスト
        print("✅ 条件検索テスト")
        results = analysis_repo.get_users_by_criteria({'university_relation': '高'})
        print(f"大学関係者（高）: {len(results)}件")
        
        # 4. 統計テスト
        print("✅ 統計テスト")
        stats = analysis_repo.get_analysis_statistics()
        print(f"総分析数: {stats['total_analyses']}")
        print(f"平均信頼度: {stats['average_confidence']:.2f}")
        
        print("🎉 AnalysisRepository テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close_connection()
        # テストファイルを削除
        if os.path.exists("test_analysis_repo.db"):
            os.remove("test_analysis_repo.db")