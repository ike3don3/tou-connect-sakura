#!/usr/bin/env python3
"""
データベース管理クラス
TOU Connect学友マッチングプラットフォームのデータベース基盤
"""
import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, Dict, List, Any
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """データベース接続と基本操作を管理するクラス"""
    
    def __init__(self, db_path: str = "tou_connect.db"):
        """
        データベースマネージャーの初期化
        
        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = db_path
        self.connection = None
        self._ensure_database_exists()
        
    def _ensure_database_exists(self):
        """データベースファイルが存在することを確認"""
        if not os.path.exists(self.db_path):
            logger.info(f"データベースファイルを作成: {self.db_path}")
            self.get_connection()
            self.create_tables()
            self.close_connection()
    
    def get_connection(self) -> sqlite3.Connection:
        """データベース接続を取得"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # 辞書形式でアクセス可能
            logger.info(f"データベースに接続: {self.db_path}")
        return self.connection
    
    def close_connection(self):
        """データベース接続を閉じる"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("データベース接続を閉じました")
    
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        SQLクエリを実行
        
        Args:
            query: 実行するSQLクエリ
            params: クエリパラメータ
            
        Returns:
            実行結果のカーソル
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error(f"SQLクエリ実行エラー: {e}")
            logger.error(f"クエリ: {query}")
            logger.error(f"パラメータ: {params}")
            raise DatabaseError(f"データベース操作エラー: {e}")
    
    def execute_many(self, query: str, params_list: List[tuple]) -> sqlite3.Cursor:
        """
        複数のSQLクエリを一括実行
        
        Args:
            query: 実行するSQLクエリ
            params_list: パラメータのリスト
            
        Returns:
            実行結果のカーソル
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error(f"一括SQLクエリ実行エラー: {e}")
            raise DatabaseError(f"データベース一括操作エラー: {e}")
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """
        単一レコードを取得
        
        Args:
            query: 実行するSQLクエリ
            params: クエリパラメータ
            
        Returns:
            取得したレコード（辞書形式）またはNone
        """
        cursor = self.execute_query(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        """
        複数レコードを取得
        
        Args:
            query: 実行するSQLクエリ
            params: クエリパラメータ
            
        Returns:
            取得したレコードのリスト（辞書形式）
        """
        cursor = self.execute_query(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def create_tables(self):
        """全テーブルを作成"""
        logger.info("データベーステーブルを作成中...")
        
        # 1. Usersテーブル
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                twitter_username VARCHAR(50) UNIQUE NOT NULL,
                twitter_id VARCHAR(50) UNIQUE,
                name VARCHAR(100),
                bio TEXT,
                location VARCHAR(100),
                followers_count INTEGER DEFAULT 0,
                following_count INTEGER DEFAULT 0,
                tweet_count INTEGER DEFAULT 0,
                verified BOOLEAN DEFAULT FALSE,
                profile_image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_analyzed_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # 2. User_Analysisテーブル
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS user_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                university_relation VARCHAR(20),
                relation_type VARCHAR(50),
                major_field VARCHAR(100),
                personality_traits TEXT,
                learning_style TEXT,
                activity_pattern TEXT,
                collaboration_potential VARCHAR(20),
                analysis_confidence REAL,
                raw_analysis_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 3. User_Interestsテーブル
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS user_interests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                interest_category VARCHAR(50),
                interest_name VARCHAR(100),
                confidence_score REAL,
                source VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 4. User_Skillsテーブル
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS user_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                skill_name VARCHAR(100),
                skill_level VARCHAR(20),
                skill_category VARCHAR(50),
                confidence_score REAL,
                source VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 5. Matching_Historyテーブル
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS matching_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                compatibility_score REAL,
                match_reasons TEXT,
                match_type VARCHAR(50),
                status VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                responded_at TIMESTAMP,
                FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 6. Communication_Suggestionsテーブル
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS communication_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                suggestion_type VARCHAR(50),
                suggestion_text TEXT,
                common_elements TEXT,
                priority_score REAL,
                is_used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 7. User_Relationshipsテーブル
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS user_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                relationship_type VARCHAR(50),
                relationship_strength REAL,
                interaction_count INTEGER DEFAULT 0,
                last_interaction_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # インデックスを作成
        self._create_indexes()
        
        logger.info("データベーステーブル作成完了")
    
    def _create_indexes(self):
        """パフォーマンス向上のためのインデックスを作成"""
        indexes = [
            # ユーザー検索用
            "CREATE INDEX IF NOT EXISTS idx_users_twitter_username ON users(twitter_username)",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_users_updated_at ON users(updated_at)",
            
            # 分析結果検索用
            "CREATE INDEX IF NOT EXISTS idx_analysis_user_id ON user_analysis(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_analysis_university_relation ON user_analysis(university_relation)",
            "CREATE INDEX IF NOT EXISTS idx_analysis_major_field ON user_analysis(major_field)",
            
            # 興味・スキル検索用
            "CREATE INDEX IF NOT EXISTS idx_interests_user_id ON user_interests(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_interests_category ON user_interests(interest_category)",
            "CREATE INDEX IF NOT EXISTS idx_skills_user_id ON user_skills(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_skills_category ON user_skills(skill_category)",
            
            # マッチング履歴用
            "CREATE INDEX IF NOT EXISTS idx_matching_user1_id ON matching_history(user1_id)",
            "CREATE INDEX IF NOT EXISTS idx_matching_user2_id ON matching_history(user2_id)",
            "CREATE INDEX IF NOT EXISTS idx_matching_status ON matching_history(status)",
            "CREATE INDEX IF NOT EXISTS idx_matching_created_at ON matching_history(created_at)",
        ]
        
        for index_sql in indexes:
            self.execute_query(index_sql)
        
        logger.info("データベースインデックス作成完了")
    
    def get_table_info(self, table_name: str) -> List[Dict]:
        """テーブル構造情報を取得"""
        return self.fetch_all(f"PRAGMA table_info({table_name})")
    
    def get_all_tables(self) -> List[str]:
        """全テーブル名を取得"""
        rows = self.fetch_all(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row['name'] for row in rows]
    
    def backup_database(self, backup_path: str):
        """データベースをバックアップ"""
        try:
            conn = self.get_connection()
            with open(backup_path, 'w') as f:
                for line in conn.iterdump():
                    f.write('%s\n' % line)
            logger.info(f"データベースバックアップ完了: {backup_path}")
        except Exception as e:
            logger.error(f"バックアップエラー: {e}")
            raise DatabaseError(f"バックアップ失敗: {e}")


class DatabaseError(Exception):
    """データベース操作エラー"""
    pass


class UserNotFoundError(DatabaseError):
    """ユーザーが見つからないエラー"""
    pass


class DuplicateUserError(DatabaseError):
    """重複ユーザーエラー"""
    pass


class AnalysisError(DatabaseError):
    """分析データエラー"""
    pass


# ユーティリティ関数
def json_to_text(data: Any) -> str:
    """JSONデータをテキストに変換"""
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    return json.dumps(data, ensure_ascii=False)


def text_to_json(text: str) -> Any:
    """テキストをJSONデータに変換"""
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


if __name__ == "__main__":
    # テスト実行
    print("🔧 データベース基盤テスト開始")
    
    # テスト用データベース
    db = DatabaseManager("test_tou_connect.db")
    
    try:
        # テーブル作成テスト
        print("✅ テーブル作成テスト")
        tables = db.get_all_tables()
        print(f"作成されたテーブル: {tables}")
        
        # 基本操作テスト
        print("✅ 基本操作テスト")
        test_user = db.fetch_one("SELECT COUNT(*) as count FROM users")
        print(f"ユーザー数: {test_user['count']}")
        
        print("🎉 データベース基盤テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
    finally:
        db.close_connection()
        # テストファイルを削除
        if os.path.exists("test_tou_connect.db"):
            os.remove("test_tou_connect.db")