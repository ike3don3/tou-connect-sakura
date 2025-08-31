"""
PrivacyManager - プライバシー・法的コンプライアンス管理クラス
GDPR準拠のデータ管理、ユーザー同意管理、データ削除機能を提供
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from flask import request, session
from database.database_manager import DatabaseManager


class PrivacyManager:
    """プライバシー・法的コンプライアンス管理クラス"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        
        # プライバシーポリシーとTOSのバージョン管理
        self.current_privacy_version = "1.0"
        self.current_terms_version = "1.0"
        
        # 必要なテーブルを作成
        self._create_privacy_tables()
    
    def _create_privacy_tables(self):
        """プライバシー関連テーブルの作成"""
        try:
            # ユーザー同意テーブル
            consent_table_sql = """
            CREATE TABLE IF NOT EXISTS user_consents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                consent_type VARCHAR(50) NOT NULL,
                consent_version VARCHAR(20) NOT NULL,
                consented_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                metadata TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
            
            # 監査ログテーブル
            audit_table_sql = """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action VARCHAR(100) NOT NULL,
                resource_type VARCHAR(50),
                resource_id INTEGER,
                metadata TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
            
            # データ削除リクエストテーブル
            deletion_table_sql = """
            CREATE TABLE IF NOT EXISTS data_deletion_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                request_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
            
            self.db.execute_query(consent_table_sql)
            self.db.execute_query(audit_table_sql)
            self.db.execute_query(deletion_table_sql)
            
            # インデックス作成
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_user_consents_user_id ON user_consents(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_consents_type ON user_consents(consent_type)",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)",
                "CREATE INDEX IF NOT EXISTS idx_deletion_requests_user_id ON data_deletion_requests(user_id)"
            ]
            
            for index_sql in indexes:
                self.db.execute_query(index_sql)
            
            self.logger.info("プライバシー関連テーブルを作成しました")
            
        except Exception as e:
            self.logger.error(f"プライバシーテーブル作成エラー: {e}")
            raise
    
    def create_consent_record(self, user_id: int, consent_type: str, 
                            consent_version: str = None, metadata: Dict = None) -> bool:
        """ユーザー同意記録の作成"""
        try:
            if consent_version is None:
                consent_version = (self.current_privacy_version if consent_type == 'privacy_policy' 
                                 else self.current_terms_version)
            
            # 既存の同意を無効化
            deactivate_sql = """
            UPDATE user_consents 
            SET is_active = FALSE 
            WHERE user_id = ? AND consent_type = ?
            """
            self.db.execute_query(deactivate_sql, (user_id, consent_type))
            
            # 新しい同意記録を作成
            insert_sql = """
            INSERT INTO user_consents 
            (user_id, consent_type, consent_version, ip_address, user_agent, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            
            ip_address = self._get_client_ip()
            user_agent = self._get_user_agent()
            metadata_json = json.dumps(metadata) if metadata else None
            
            self.db.execute_query(insert_sql, (
                user_id, consent_type, consent_version, 
                ip_address, user_agent, metadata_json
            ))
            
            # 監査ログに記録
            self.log_user_action(
                user_id, 
                f"consent_given_{consent_type}", 
                "consent", 
                None,
                {"version": consent_version}
            )
            
            self.logger.info(f"ユーザー {user_id} の同意記録を作成: {consent_type} v{consent_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"同意記録作成エラー: {e}")
            return False
    
    def get_user_consents(self, user_id: int) -> List[Dict]:
        """ユーザーの同意状況を取得"""
        try:
            sql = """
            SELECT consent_type, consent_version, consented_at, is_active
            FROM user_consents 
            WHERE user_id = ? AND is_active = TRUE
            ORDER BY consented_at DESC
            """
            
            results = self.db.fetch_all(sql, (user_id,))
            return [dict(row) for row in results] if results else []
            
        except Exception as e:
            self.logger.error(f"同意状況取得エラー: {e}")
            return []
    
    def check_consent_required(self, user_id: int) -> Dict[str, bool]:
        """同意が必要かどうかをチェック"""
        try:
            consents = self.get_user_consents(user_id)
            consent_status = {
                'privacy_policy': False,
                'terms_of_service': False
            }
            
            for consent in consents:
                consent_type = consent['consent_type']
                consent_version = consent['consent_version']
                
                # 現在のバージョンと比較
                current_version = (self.current_privacy_version if consent_type == 'privacy_policy' 
                                 else self.current_terms_version)
                
                if consent_version == current_version:
                    consent_status[consent_type] = True
            
            return {
                'privacy_policy_required': not consent_status['privacy_policy'],
                'terms_required': not consent_status['terms_of_service'],
                'any_required': not all(consent_status.values())
            }
            
        except Exception as e:
            self.logger.error(f"同意チェックエラー: {e}")
            return {
                'privacy_policy_required': True,
                'terms_required': True,
                'any_required': True
            }
    
    def delete_user_data(self, user_id: int, deletion_type: str = "complete") -> bool:
        """ユーザーデータの完全削除（GDPR準拠）"""
        try:
            # 削除リクエストを記録
            self._create_deletion_request(user_id, deletion_type)
            
            if deletion_type == "complete":
                # 完全削除: すべてのデータを削除
                tables_to_delete = [
                    "user_interests",
                    "user_skills", 
                    "user_analyses",
                    "resource_clicks",
                    "user_consents",
                    "audit_logs"
                ]
                
                for table in tables_to_delete:
                    try:
                        delete_sql = f"DELETE FROM {table} WHERE user_id = ?"
                        self.db.execute_query(delete_sql, (user_id,))
                    except Exception as e:
                        self.logger.warning(f"テーブル {table} からの削除でエラー: {e}")
                
                # ユーザーテーブルからも削除
                self.db.execute_query("DELETE FROM users WHERE id = ?", (user_id,))
                
            elif deletion_type == "anonymize":
                # 匿名化: 個人識別情報のみ削除
                self.anonymize_user_data(user_id)
            
            # 削除リクエストのステータスを更新
            self._update_deletion_request_status(user_id, "completed")
            
            self.logger.info(f"ユーザー {user_id} のデータ削除完了: {deletion_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"データ削除エラー: {e}")
            self._update_deletion_request_status(user_id, "failed")
            return False
    
    def anonymize_user_data(self, user_id: int) -> bool:
        """ユーザーデータの匿名化"""
        try:
            # ユーザー情報の匿名化
            anonymize_sql = """
            UPDATE users SET 
                name = 'Anonymous User',
                twitter_username = CONCAT('anon_', id),
                bio = '[Anonymized]',
                location = '[Anonymized]',
                profile_image_url = NULL,
                is_active = FALSE,
                anonymized_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            
            self.db.execute_query(anonymize_sql, (user_id,))
            
            # 監査ログに記録
            self.log_user_action(user_id, "data_anonymized", "user", user_id)
            
            self.logger.info(f"ユーザー {user_id} のデータを匿名化しました")
            return True
            
        except Exception as e:
            self.logger.error(f"データ匿名化エラー: {e}")
            return False
    
    def export_user_data(self, user_id: int) -> Dict[str, Any]:
        """ユーザーデータのエクスポート（GDPR準拠）"""
        try:
            export_data = {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "data": {}
            }
            
            # ユーザー基本情報
            user_sql = "SELECT * FROM users WHERE id = ?"
            user_data = self.db.fetch_one(user_sql, (user_id,))
            if user_data:
                export_data["data"]["user_profile"] = dict(user_data)
            
            # 分析結果
            analysis_sql = "SELECT * FROM user_analyses WHERE user_id = ?"
            analyses = self.db.fetch_all(analysis_sql, (user_id,))
            if analyses:
                export_data["data"]["analyses"] = [dict(row) for row in analyses]
            
            # 興味・スキル
            interests_sql = "SELECT * FROM user_interests WHERE user_id = ?"
            interests = self.db.fetch_all(interests_sql, (user_id,))
            if interests:
                export_data["data"]["interests"] = [dict(row) for row in interests]
            
            skills_sql = "SELECT * FROM user_skills WHERE user_id = ?"
            skills = self.db.fetch_all(skills_sql, (user_id,))
            if skills:
                export_data["data"]["skills"] = [dict(row) for row in skills]
            
            # 同意記録
            consents_sql = "SELECT * FROM user_consents WHERE user_id = ?"
            consents = self.db.fetch_all(consents_sql, (user_id,))
            if consents:
                export_data["data"]["consents"] = [dict(row) for row in consents]
            
            # リソースクリック履歴
            clicks_sql = "SELECT * FROM resource_clicks WHERE user_id = ?"
            clicks = self.db.fetch_all(clicks_sql, (user_id,))
            if clicks:
                export_data["data"]["resource_clicks"] = [dict(row) for row in clicks]
            
            # 監査ログに記録
            self.log_user_action(user_id, "data_exported", "user", user_id)
            
            self.logger.info(f"ユーザー {user_id} のデータエクスポート完了")
            return export_data
            
        except Exception as e:
            self.logger.error(f"データエクスポートエラー: {e}")
            return {"error": str(e)}
    
    def log_user_action(self, user_id: int, action: str, resource_type: str = None, 
                       resource_id: int = None, metadata: Dict = None):
        """ユーザーアクションの監査ログ記録"""
        try:
            sql = """
            INSERT INTO audit_logs 
            (user_id, action, resource_type, resource_id, metadata, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            ip_address = self._get_client_ip()
            user_agent = self._get_user_agent()
            metadata_json = json.dumps(metadata) if metadata else None
            
            self.db.execute_query(sql, (
                user_id, action, resource_type, resource_id, 
                metadata_json, ip_address, user_agent
            ))
            
        except Exception as e:
            self.logger.error(f"監査ログ記録エラー: {e}")
    
    def get_audit_logs(self, user_id: int, limit: int = 100) -> List[Dict]:
        """ユーザーの監査ログを取得"""
        try:
            sql = """
            SELECT action, resource_type, resource_id, metadata, 
                   ip_address, created_at
            FROM audit_logs 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
            """
            
            results = self.db.fetch_all(sql, (user_id, limit))
            return [dict(row) for row in results] if results else []
            
        except Exception as e:
            self.logger.error(f"監査ログ取得エラー: {e}")
            return []
    
    def _create_deletion_request(self, user_id: int, deletion_type: str):
        """データ削除リクエストの作成"""
        try:
            sql = """
            INSERT INTO data_deletion_requests 
            (user_id, request_type, metadata)
            VALUES (?, ?, ?)
            """
            
            metadata = {
                "ip_address": self._get_client_ip(),
                "user_agent": self._get_user_agent(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self.db.execute_query(sql, (user_id, deletion_type, json.dumps(metadata)))
            
        except Exception as e:
            self.logger.error(f"削除リクエスト作成エラー: {e}")
    
    def _update_deletion_request_status(self, user_id: int, status: str):
        """削除リクエストのステータス更新"""
        try:
            sql = """
            UPDATE data_deletion_requests 
            SET status = ?, processed_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND status = 'pending'
            """
            
            self.db.execute_query(sql, (status, user_id))
            
        except Exception as e:
            self.logger.error(f"削除リクエストステータス更新エラー: {e}")
    
    def _get_client_ip(self) -> str:
        """クライアントIPアドレスの取得"""
        try:
            if request:
                # プロキシ経由の場合のIP取得
                if request.headers.get('X-Forwarded-For'):
                    return request.headers.get('X-Forwarded-For').split(',')[0].strip()
                elif request.headers.get('X-Real-IP'):
                    return request.headers.get('X-Real-IP')
                else:
                    return request.remote_addr
            return "unknown"
        except:
            return "unknown"
    
    def _get_user_agent(self) -> str:
        """ユーザーエージェントの取得"""
        try:
            if request:
                return request.headers.get('User-Agent', 'unknown')
            return "unknown"
        except:
            return "unknown"
    
    def cleanup_old_logs(self, days: int = 365):
        """古い監査ログのクリーンアップ"""
        try:
            sql = """
            DELETE FROM audit_logs 
            WHERE created_at < datetime('now', '-{} days')
            """.format(days)
            
            self.db.execute_query(sql)
            self.logger.info(f"{days}日以前の監査ログをクリーンアップしました")
            
        except Exception as e:
            self.logger.error(f"ログクリーンアップエラー: {e}")
    
    def get_privacy_statistics(self) -> Dict[str, Any]:
        """プライバシー関連の統計情報"""
        try:
            stats = {}
            
            # 同意統計
            consent_sql = """
            SELECT consent_type, COUNT(*) as count
            FROM user_consents 
            WHERE is_active = TRUE
            GROUP BY consent_type
            """
            consent_stats = self.db.fetch_all(consent_sql)
            stats["consents"] = {row["consent_type"]: row["count"] for row in consent_stats}
            
            # 削除リクエスト統計
            deletion_sql = """
            SELECT status, COUNT(*) as count
            FROM data_deletion_requests
            GROUP BY status
            """
            deletion_stats = self.db.fetch_all(deletion_sql)
            stats["deletion_requests"] = {row["status"]: row["count"] for row in deletion_stats}
            
            return stats
            
        except Exception as e:
            self.logger.error(f"統計情報取得エラー: {e}")
            return {}