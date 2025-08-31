"""
SchemaManager - データベーススキーマ管理クラス
本番環境用のテーブル作成、インデックス最適化、マイグレーション機能を提供
"""
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any
from database.production_database_manager import ProductionDatabaseManager


class SchemaManager:
    """データベーススキーマ管理クラス"""
    
    def __init__(self, db_manager: ProductionDatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        
        # スキーマバージョン管理
        self.current_schema_version = "1.0.0"
        self.migration_history = []
    
    def create_production_schema(self):
        """本番環境用スキーマの作成"""
        try:
            self.logger.info("Creating production database schema...")
            
            # 基本テーブルの作成
            self._create_core_tables()
            
            # プライバシー関連テーブルの作成
            self._create_privacy_tables()
            
            # システム管理テーブルの作成
            self._create_system_tables()
            
            # インデックスの作成
            self._create_indexes()
            
            # 制約の作成
            self._create_constraints()
            
            # スキーマバージョンの記録
            self._record_schema_version()
            
            self.logger.info("Production database schema created successfully")
            
        except Exception as e:
            self.logger.error(f"Schema creation failed: {e}")
            raise
    
    def _create_core_tables(self):
        """コアテーブルの作成"""
        
        # ユーザーテーブル（拡張版）
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            twitter_username VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            bio TEXT,
            location VARCHAR(100),
            followers_count INTEGER DEFAULT 0,
            following_count INTEGER DEFAULT 0,
            tweet_count INTEGER DEFAULT 0,
            verified BOOLEAN DEFAULT FALSE,
            profile_image_url TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            anonymized_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # ユーザー分析テーブル（拡張版）
        user_analyses_table = """
        CREATE TABLE IF NOT EXISTS user_analyses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            analysis_type VARCHAR(50) DEFAULT 'twitter_profile',
            analysis_data JSONB NOT NULL,
            university_relation VARCHAR(20),
            relation_type VARCHAR(50),
            major_field VARCHAR(50),
            confidence_score DECIMAL(3,2),
            analysis_version VARCHAR(10) DEFAULT '1.0',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
        
        # ユーザー興味テーブル（拡張版）
        user_interests_table = """
        CREATE TABLE IF NOT EXISTS user_interests (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            interest_category VARCHAR(50) NOT NULL,
            interest_name VARCHAR(100) NOT NULL,
            confidence_score DECIMAL(3,2) DEFAULT 0.5,
            source VARCHAR(50) DEFAULT 'ai_analysis',
            is_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
        
        # ユーザースキルテーブル（拡張版）
        user_skills_table = """
        CREATE TABLE IF NOT EXISTS user_skills (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            skill_category VARCHAR(50) NOT NULL,
            skill_name VARCHAR(100) NOT NULL,
            proficiency_level VARCHAR(20) DEFAULT 'beginner',
            confidence_score DECIMAL(3,2) DEFAULT 0.5,
            source VARCHAR(50) DEFAULT 'ai_analysis',
            is_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
        
        # リソースクリックテーブル（拡張版）
        resource_clicks_table = """
        CREATE TABLE IF NOT EXISTS resource_clicks (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            resource_title VARCHAR(200) NOT NULL,
            resource_url TEXT NOT NULL,
            affiliate_url TEXT,
            click_source VARCHAR(50) DEFAULT 'recommendation',
            conversion_tracked BOOLEAN DEFAULT FALSE,
            revenue_amount DECIMAL(10,2),
            ip_address INET,
            user_agent TEXT,
            clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
        
        # アフィリエイトクリックテーブル
        affiliate_clicks_table = """
        CREATE TABLE IF NOT EXISTS affiliate_clicks (
            id SERIAL PRIMARY KEY,
            click_id VARCHAR(36) UNIQUE NOT NULL,
            user_id INTEGER,
            session_id VARCHAR(255) NOT NULL,
            affiliate_id VARCHAR(100) NOT NULL,
            resource_id VARCHAR(255) NOT NULL,
            resource_url TEXT NOT NULL,
            source VARCHAR(50) NOT NULL,
            clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address INET,
            user_agent TEXT,
            referrer TEXT,
            metadata JSONB,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
        
        # アフィリエイトコンバージョンテーブル
        affiliate_conversions_table = """
        CREATE TABLE IF NOT EXISTS affiliate_conversions (
            id SERIAL PRIMARY KEY,
            conversion_id VARCHAR(36) UNIQUE NOT NULL,
            click_id VARCHAR(36) NOT NULL,
            user_id INTEGER,
            affiliate_id VARCHAR(100) NOT NULL,
            conversion_type VARCHAR(50) NOT NULL,
            conversion_value DECIMAL(10,2) NOT NULL,
            currency VARCHAR(3) DEFAULT 'JPY',
            converted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (click_id) REFERENCES affiliate_clicks(click_id)
        )
        """
        
        tables = [
            ("users", users_table),
            ("user_analyses", user_analyses_table),
            ("user_interests", user_interests_table),
            ("user_skills", user_skills_table),
            ("resource_clicks", resource_clicks_table),
            ("affiliate_clicks", affiliate_clicks_table),
            ("affiliate_conversions", affiliate_conversions_table)
        ]
        
        for table_name, table_sql in tables:
            try:
                # PostgreSQL/MySQL用のSQLをSQLite用に調整
                if self.db.db_type == 'sqlite':
                    table_sql = self._convert_to_sqlite(table_sql)
                
                self.db.execute_with_retry(table_sql)
                self.logger.info(f"Created table: {table_name}")
            except Exception as e:
                self.logger.error(f"Failed to create table {table_name}: {e}")
                raise
    
    def _create_privacy_tables(self):
        """プライバシー関連テーブルの作成"""
        
        # ユーザー同意テーブル（拡張版）
        user_consents_table = """
        CREATE TABLE IF NOT EXISTS user_consents (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            consent_type VARCHAR(50) NOT NULL,
            consent_version VARCHAR(20) NOT NULL,
            consented_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address INET,
            user_agent TEXT,
            metadata JSONB,
            is_active BOOLEAN DEFAULT TRUE,
            withdrawn_at TIMESTAMP NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
        
        # 監査ログテーブル（拡張版）
        audit_logs_table = """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(50),
            resource_id INTEGER,
            metadata JSONB,
            ip_address INET,
            user_agent TEXT,
            session_id VARCHAR(100),
            severity VARCHAR(20) DEFAULT 'info',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        )
        """
        
        # データ削除リクエストテーブル（拡張版）
        data_deletion_requests_table = """
        CREATE TABLE IF NOT EXISTS data_deletion_requests (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            request_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP NULL,
            processed_by VARCHAR(100),
            metadata JSONB,
            deletion_reason TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
        
        tables = [
            ("user_consents", user_consents_table),
            ("audit_logs", audit_logs_table),
            ("data_deletion_requests", data_deletion_requests_table)
        ]
        
        for table_name, table_sql in tables:
            try:
                if self.db.db_type == 'sqlite':
                    table_sql = self._convert_to_sqlite(table_sql)
                
                self.db.execute_with_retry(table_sql)
                self.logger.info(f"Created privacy table: {table_name}")
            except Exception as e:
                self.logger.error(f"Failed to create privacy table {table_name}: {e}")
                raise
    
    def _create_system_tables(self):
        """システム管理テーブルの作成"""
        
        # システムメトリクステーブル（拡張版）
        system_metrics_table = """
        CREATE TABLE IF NOT EXISTS system_metrics (
            id SERIAL PRIMARY KEY,
            metric_name VARCHAR(100) NOT NULL,
            metric_value DECIMAL(15,4),
            metric_type VARCHAR(20) DEFAULT 'gauge',
            tags JSONB,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NULL
        )
        """
        
        # スキーマバージョンテーブル
        schema_versions_table = """
        CREATE TABLE IF NOT EXISTS schema_versions (
            id SERIAL PRIMARY KEY,
            version VARCHAR(20) NOT NULL,
            description TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rollback_sql TEXT
        )
        """
        
        # システム設定テーブル
        system_settings_table = """
        CREATE TABLE IF NOT EXISTS system_settings (
            id SERIAL PRIMARY KEY,
            setting_key VARCHAR(100) UNIQUE NOT NULL,
            setting_value JSONB NOT NULL,
            description TEXT,
            is_encrypted BOOLEAN DEFAULT FALSE,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by VARCHAR(100)
        )
        """
        
        tables = [
            ("system_metrics", system_metrics_table),
            ("schema_versions", schema_versions_table),
            ("system_settings", system_settings_table)
        ]
        
        for table_name, table_sql in tables:
            try:
                if self.db.db_type == 'sqlite':
                    table_sql = self._convert_to_sqlite(table_sql)
                
                self.db.execute_with_retry(table_sql)
                self.logger.info(f"Created system table: {table_name}")
            except Exception as e:
                self.logger.error(f"Failed to create system table {table_name}: {e}")
                raise
    
    def _create_indexes(self):
        """インデックスの作成"""
        
        indexes = [
            # ユーザーテーブルのインデックス
            "CREATE INDEX IF NOT EXISTS idx_users_twitter_username ON users(twitter_username)",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
            
            # 分析テーブルのインデックス
            "CREATE INDEX IF NOT EXISTS idx_user_analyses_user_id ON user_analyses(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_analyses_type ON user_analyses(analysis_type)",
            "CREATE INDEX IF NOT EXISTS idx_user_analyses_created_at ON user_analyses(created_at)",
            
            # 興味テーブルのインデックス
            "CREATE INDEX IF NOT EXISTS idx_user_interests_user_id ON user_interests(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_interests_category ON user_interests(interest_category)",
            "CREATE INDEX IF NOT EXISTS idx_user_interests_confidence ON user_interests(confidence_score)",
            
            # スキルテーブルのインデックス
            "CREATE INDEX IF NOT EXISTS idx_user_skills_user_id ON user_skills(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_skills_category ON user_skills(skill_category)",
            "CREATE INDEX IF NOT EXISTS idx_user_skills_proficiency ON user_skills(proficiency_level)",
            
            # リソースクリックのインデックス
            "CREATE INDEX IF NOT EXISTS idx_resource_clicks_user_id ON resource_clicks(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_resource_clicks_clicked_at ON resource_clicks(clicked_at)",
            "CREATE INDEX IF NOT EXISTS idx_resource_clicks_conversion ON resource_clicks(conversion_tracked)",
            
            # 同意テーブルのインデックス
            "CREATE INDEX IF NOT EXISTS idx_user_consents_user_id ON user_consents(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_consents_type ON user_consents(consent_type)",
            "CREATE INDEX IF NOT EXISTS idx_user_consents_active ON user_consents(is_active)",
            
            # 監査ログのインデックス
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_severity ON audit_logs(severity)",
            
            # システムメトリクスのインデックス
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name)",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_recorded_at ON system_metrics(recorded_at)",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_expires_at ON system_metrics(expires_at)",
            
            # アフィリエイトクリックのインデックス
            "CREATE INDEX IF NOT EXISTS idx_affiliate_clicks_click_id ON affiliate_clicks(click_id)",
            "CREATE INDEX IF NOT EXISTS idx_affiliate_clicks_user_id ON affiliate_clicks(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_affiliate_clicks_affiliate_id ON affiliate_clicks(affiliate_id)",
            "CREATE INDEX IF NOT EXISTS idx_affiliate_clicks_clicked_at ON affiliate_clicks(clicked_at)",
            "CREATE INDEX IF NOT EXISTS idx_affiliate_clicks_source ON affiliate_clicks(source)",
            
            # アフィリエイトコンバージョンのインデックス
            "CREATE INDEX IF NOT EXISTS idx_affiliate_conversions_conversion_id ON affiliate_conversions(conversion_id)",
            "CREATE INDEX IF NOT EXISTS idx_affiliate_conversions_click_id ON affiliate_conversions(click_id)",
            "CREATE INDEX IF NOT EXISTS idx_affiliate_conversions_user_id ON affiliate_conversions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_affiliate_conversions_affiliate_id ON affiliate_conversions(affiliate_id)",
            "CREATE INDEX IF NOT EXISTS idx_affiliate_conversions_converted_at ON affiliate_conversions(converted_at)",
            "CREATE INDEX IF NOT EXISTS idx_affiliate_conversions_type ON affiliate_conversions(conversion_type)"
        ]
        
        for index_sql in indexes:
            try:
                self.db.execute_with_retry(index_sql)
                self.logger.debug(f"Created index: {index_sql.split()[5]}")
            except Exception as e:
                self.logger.warning(f"Failed to create index: {e}")
        
        self.logger.info("Database indexes created successfully")
    
    def _create_constraints(self):
        """制約の作成"""
        
        # PostgreSQL/MySQLの場合のみ制約を追加
        if self.db.db_type in ['postgresql', 'mysql']:
            constraints = [
                # ユニーク制約
                "ALTER TABLE user_interests ADD CONSTRAINT uk_user_interests_user_category_name UNIQUE (user_id, interest_category, interest_name)",
                "ALTER TABLE user_skills ADD CONSTRAINT uk_user_skills_user_category_name UNIQUE (user_id, skill_category, skill_name)",
                
                # チェック制約
                "ALTER TABLE user_analyses ADD CONSTRAINT chk_confidence_score CHECK (confidence_score >= 0 AND confidence_score <= 1)",
                "ALTER TABLE user_interests ADD CONSTRAINT chk_interest_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1)",
                "ALTER TABLE user_skills ADD CONSTRAINT chk_skill_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1)"
            ]
            
            for constraint_sql in constraints:
                try:
                    self.db.execute_with_retry(constraint_sql)
                    self.logger.debug(f"Created constraint: {constraint_sql.split()[4]}")
                except Exception as e:
                    self.logger.warning(f"Failed to create constraint: {e}")
            
            self.logger.info("Database constraints created successfully")
    
    def _convert_to_sqlite(self, sql: str) -> str:
        """PostgreSQL/MySQL SQLをSQLite用に変換"""
        # SERIAL -> INTEGER PRIMARY KEY AUTOINCREMENT
        sql = sql.replace('SERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
        
        # JSONB -> TEXT (SQLiteはJSONBをサポートしていない)
        sql = sql.replace('JSONB', 'TEXT')
        
        # INET -> TEXT (SQLiteはINETをサポートしていない)
        sql = sql.replace('INET', 'TEXT')
        
        # DECIMAL -> REAL
        sql = sql.replace('DECIMAL(15,4)', 'REAL')
        sql = sql.replace('DECIMAL(10,2)', 'REAL')
        sql = sql.replace('DECIMAL(3,2)', 'REAL')
        
        # ON DELETE CASCADE/SET NULL (SQLiteでは制限あり)
        sql = sql.replace('ON DELETE CASCADE', '')
        sql = sql.replace('ON DELETE SET NULL', '')
        
        return sql
    
    def _record_schema_version(self):
        """スキーマバージョンの記録"""
        try:
            version_sql = """
            INSERT INTO schema_versions (version, description)
            VALUES (?, ?)
            """
            
            self.db.execute_with_retry(
                version_sql,
                (self.current_schema_version, "Initial production schema")
            )
            
            self.logger.info(f"Schema version {self.current_schema_version} recorded")
            
        except Exception as e:
            self.logger.error(f"Failed to record schema version: {e}")
    
    def get_schema_info(self) -> Dict[str, Any]:
        """スキーマ情報の取得"""
        try:
            # テーブル一覧
            if self.db.db_type == 'postgresql':
                tables_query = """
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
            elif self.db.db_type == 'mysql':
                tables_query = """
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                ORDER BY table_name
                """
            else:
                tables_query = """
                SELECT name as table_name, type as table_type 
                FROM sqlite_master 
                WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            
            tables = self.db.fetch_all_with_retry(tables_query)
            
            # スキーマバージョン
            version_query = """
            SELECT version, applied_at 
            FROM schema_versions 
            ORDER BY applied_at DESC 
            LIMIT 1
            """
            
            try:
                current_version = self.db.fetch_one_with_retry(version_query)
            except:
                current_version = None
            
            return {
                'current_version': current_version['version'] if current_version else 'unknown',
                'applied_at': current_version['applied_at'] if current_version else None,
                'total_tables': len(tables),
                'tables': tables,
                'database_type': self.db.db_type
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get schema info: {e}")
            return {'error': str(e)}
    
    def optimize_database(self):
        """データベース最適化"""
        try:
            if self.db.db_type == 'postgresql':
                self._optimize_postgresql()
            elif self.db.db_type == 'mysql':
                self._optimize_mysql()
            else:
                self._optimize_sqlite()
                
            self.logger.info("Database optimization completed")
            
        except Exception as e:
            self.logger.error(f"Database optimization failed: {e}")
    
    def _optimize_postgresql(self):
        """PostgreSQL最適化"""
        # VACUUM ANALYZE
        self.db.execute_with_retry("VACUUM ANALYZE")
        
        # 統計情報の更新
        self.db.execute_with_retry("ANALYZE")
        
        self.logger.info("PostgreSQL optimization completed")
    
    def _optimize_mysql(self):
        """MySQL最適化"""
        # テーブル最適化
        tables = self.db.fetch_all_with_retry("SHOW TABLES")
        
        for table in tables:
            table_name = list(table.values())[0]
            self.db.execute_with_retry(f"OPTIMIZE TABLE {table_name}")
        
        self.logger.info("MySQL optimization completed")
    
    def _optimize_sqlite(self):
        """SQLite最適化"""
        # VACUUM
        self.db.execute_with_retry("VACUUM")
        
        # 統計情報の更新
        self.db.execute_with_retry("ANALYZE")
        
        self.logger.info("SQLite optimization completed")