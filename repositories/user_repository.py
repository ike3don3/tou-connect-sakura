#!/usr/bin/env python3
"""
ユーザーリポジトリクラス
Usersテーブルの操作を管理
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime
from typing import Optional, Dict, List, Any
import logging
from database.database_manager import DatabaseManager, UserNotFoundError, DuplicateUserError

logger = logging.getLogger(__name__)

class UserRepository:
    """ユーザーデータの永続化を管理するリポジトリクラス"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        ユーザーリポジトリの初期化
        
        Args:
            db_manager: データベースマネージャーインスタンス
        """
        self.db = db_manager
    
    def create_user(self, twitter_data: Dict[str, Any]) -> int:
        """
        新しいユーザーを作成
        
        Args:
            twitter_data: Twitter APIから取得したユーザーデータ
            
        Returns:
            作成されたユーザーのID
            
        Raises:
            DuplicateUserError: ユーザーが既に存在する場合
        """
        try:
            # 既存ユーザーチェック
            existing_user = self.get_user_by_username(twitter_data.get('username', ''))
            if existing_user:
                raise DuplicateUserError(f"ユーザー @{twitter_data['username']} は既に存在します")
            
            # ユーザーデータを挿入
            query = """
                INSERT INTO users (
                    twitter_username, twitter_id, name, bio, location,
                    followers_count, following_count, tweet_count, verified,
                    profile_image_url, updated_at, last_analyzed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                twitter_data.get('username', ''),
                twitter_data.get('id', ''),
                twitter_data.get('name', ''),
                twitter_data.get('description', ''),
                twitter_data.get('location', ''),
                twitter_data.get('followers_count', 0),
                twitter_data.get('following_count', 0),
                twitter_data.get('tweet_count', 0),
                twitter_data.get('verified', False),
                twitter_data.get('profile_image_url', ''),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            )
            
            cursor = self.db.execute_query(query, params)
            user_id = cursor.lastrowid
            
            logger.info(f"新しいユーザーを作成: @{twitter_data['username']} (ID: {user_id})")
            return user_id
            
        except Exception as e:
            logger.error(f"ユーザー作成エラー: {e}")
            raise
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        ユーザー名でユーザーを取得
        
        Args:
            username: Twitterユーザー名（@マークなし）
            
        Returns:
            ユーザーデータ（辞書形式）またはNone
        """
        query = "SELECT * FROM users WHERE twitter_username = ? AND is_active = TRUE"
        return self.db.fetch_one(query, (username,))
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        ユーザーIDでユーザーを取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            ユーザーデータ（辞書形式）またはNone
        """
        query = "SELECT * FROM users WHERE id = ? AND is_active = TRUE"
        return self.db.fetch_one(query, (user_id,))
    
    def update_user(self, user_id: int, twitter_data: Dict[str, Any]) -> bool:
        """
        ユーザー情報を更新
        
        Args:
            user_id: 更新するユーザーのID
            twitter_data: 新しいTwitterデータ
            
        Returns:
            更新成功の場合True
            
        Raises:
            UserNotFoundError: ユーザーが見つからない場合
        """
        try:
            # ユーザー存在確認
            existing_user = self.get_user_by_id(user_id)
            if not existing_user:
                raise UserNotFoundError(f"ユーザーID {user_id} が見つかりません")
            
            # 更新クエリ
            query = """
                UPDATE users SET
                    name = ?, bio = ?, location = ?,
                    followers_count = ?, following_count = ?, tweet_count = ?,
                    verified = ?, profile_image_url = ?,
                    updated_at = ?, last_analyzed_at = ?
                WHERE id = ?
            """
            
            params = (
                twitter_data.get('name', existing_user['name']),
                twitter_data.get('description', existing_user['bio']),
                twitter_data.get('location', existing_user['location']),
                twitter_data.get('followers_count', existing_user['followers_count']),
                twitter_data.get('following_count', existing_user['following_count']),
                twitter_data.get('tweet_count', existing_user['tweet_count']),
                twitter_data.get('verified', existing_user['verified']),
                twitter_data.get('profile_image_url', existing_user['profile_image_url']),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                user_id
            )
            
            self.db.execute_query(query, params)
            logger.info(f"ユーザー情報を更新: ID {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"ユーザー更新エラー: {e}")
            raise
    
    def create_or_update_user(self, twitter_data: Dict[str, Any]) -> int:
        """
        ユーザーを作成または更新（upsert操作）
        
        Args:
            twitter_data: Twitter APIから取得したユーザーデータ
            
        Returns:
            ユーザーID
        """
        username = twitter_data.get('username', '')
        existing_user = self.get_user_by_username(username)
        
        if existing_user:
            # 既存ユーザーを更新
            self.update_user(existing_user['id'], twitter_data)
            return existing_user['id']
        else:
            # 新しいユーザーを作成
            return self.create_user(twitter_data)
    
    def delete_user(self, user_id: int) -> bool:
        """
        ユーザーを論理削除（is_activeをFalseに設定）
        
        Args:
            user_id: 削除するユーザーのID
            
        Returns:
            削除成功の場合True
        """
        try:
            query = "UPDATE users SET is_active = FALSE, updated_at = ? WHERE id = ?"
            params = (datetime.now().isoformat(), user_id)
            
            cursor = self.db.execute_query(query, params)
            if cursor.rowcount > 0:
                logger.info(f"ユーザーを論理削除: ID {user_id}")
                return True
            else:
                logger.warning(f"削除対象ユーザーが見つかりません: ID {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"ユーザー削除エラー: {e}")
            raise
    
    def search_users(self, filters: Dict[str, Any], limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        条件に基づいてユーザーを検索
        
        Args:
            filters: 検索条件の辞書
            limit: 取得する最大件数
            offset: オフセット（ページネーション用）
            
        Returns:
            検索結果のユーザーリスト
        """
        try:
            # 基本クエリ
            query = "SELECT * FROM users WHERE is_active = TRUE"
            params = []
            
            # 検索条件を追加
            if filters.get('location'):
                query += " AND location LIKE ?"
                params.append(f"%{filters['location']}%")
            
            if filters.get('verified') is not None:
                query += " AND verified = ?"
                params.append(filters['verified'])
            
            if filters.get('min_followers'):
                query += " AND followers_count >= ?"
                params.append(filters['min_followers'])
            
            if filters.get('max_followers'):
                query += " AND followers_count <= ?"
                params.append(filters['max_followers'])
            
            if filters.get('name_contains'):
                query += " AND name LIKE ?"
                params.append(f"%{filters['name_contains']}%")
            
            if filters.get('bio_contains'):
                query += " AND bio LIKE ?"
                params.append(f"%{filters['bio_contains']}%")
            
            # ソートとページネーション
            query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            results = self.db.fetch_all(query, tuple(params))
            logger.info(f"ユーザー検索結果: {len(results)}件")
            return results
            
        except Exception as e:
            logger.error(f"ユーザー検索エラー: {e}")
            raise
    
    def get_user_count(self) -> int:
        """
        アクティブなユーザー数を取得
        
        Returns:
            ユーザー数
        """
        result = self.db.fetch_one("SELECT COUNT(*) as count FROM users WHERE is_active = TRUE")
        return result['count'] if result else 0
    
    def get_recent_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        最近追加されたユーザーを取得
        
        Args:
            limit: 取得する件数
            
        Returns:
            最近のユーザーリスト
        """
        query = """
            SELECT * FROM users 
            WHERE is_active = TRUE 
            ORDER BY created_at DESC 
            LIMIT ?
        """
        return self.db.fetch_all(query, (limit,))
    
    def get_users_need_update(self, hours_threshold: int = 24) -> List[Dict[str, Any]]:
        """
        更新が必要なユーザーを取得（指定時間以上更新されていない）
        
        Args:
            hours_threshold: 更新が必要と判断する時間（時間）
            
        Returns:
            更新が必要なユーザーリスト
        """
        query = """
            SELECT * FROM users 
            WHERE is_active = TRUE 
            AND datetime(last_analyzed_at) < datetime('now', '-{} hours')
            ORDER BY last_analyzed_at ASC
        """.format(hours_threshold)
        
        return self.db.fetch_all(query)


if __name__ == "__main__":
    # テスト実行
    print("🧪 UserRepository テスト開始")
    
    # テスト用データベース
    db = DatabaseManager("test_user_repo.db")
    user_repo = UserRepository(db)
    
    try:
        # テストデータ
        test_twitter_data = {
            'username': 'test_user',
            'id': '123456789',
            'name': 'テストユーザー',
            'description': '東京通信大学でプログラミングを学んでいます',
            'location': '東京',
            'followers_count': 100,
            'following_count': 200,
            'tweet_count': 500,
            'verified': False,
            'profile_image_url': 'https://example.com/image.jpg'
        }
        
        # 1. ユーザー作成テスト
        print("✅ ユーザー作成テスト")
        user_id = user_repo.create_user(test_twitter_data)
        print(f"作成されたユーザーID: {user_id}")
        
        # 2. ユーザー取得テスト
        print("✅ ユーザー取得テスト")
        user = user_repo.get_user_by_username('test_user')
        print(f"取得したユーザー: {user['name']}")
        
        # 3. ユーザー更新テスト
        print("✅ ユーザー更新テスト")
        updated_data = test_twitter_data.copy()
        updated_data['followers_count'] = 150
        user_repo.update_user(user_id, updated_data)
        
        # 4. 検索テスト
        print("✅ ユーザー検索テスト")
        results = user_repo.search_users({'location': '東京'})
        print(f"検索結果: {len(results)}件")
        
        # 5. 統計テスト
        print("✅ 統計テスト")
        count = user_repo.get_user_count()
        print(f"総ユーザー数: {count}")
        
        print("🎉 UserRepository テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
    finally:
        db.close_connection()
        # テストファイルを削除
        if os.path.exists("test_user_repo.db"):
            os.remove("test_user_repo.db")