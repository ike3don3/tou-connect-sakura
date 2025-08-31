"""
ProductionDatabaseManager - 本番環境用データベース管理クラス
PostgreSQL対応、接続プール、バックアップ機能を提供
"""
import os
import json
import logging
import time
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from database.database_manager import DatabaseManager


class ProductionDatabaseManager(DatabaseManager):
    """本番環境用データベース管理クラス"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.logger = logging.getLogger(__name__)
        
        # 接続文字列の解析
        self.db_config = self._parse_connection_string(connection_string)
        self.db_type = self.db_config.get('type', 'sqlite')
        
        # 接続プール設定
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '20'))
        self.pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
        self.pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '3600'))
        
        # 接続プールの初期化
        self.connection_pool = None
        self.backup_manager = BackupManager(self)
        
        # 統計情報
        self.stats = {
            'total_queries': 0,
            'failed_queries': 0,
            'connection_errors': 0,
            'last_backup': None,
            'uptime_start': time.time()
        }
        
        # 初期化
        self._init_connection_pool()
        super().__init__(self._get_db_path())
    
    def _parse_connection_string(self, connection_string: str) -> Dict[str, str]:
        """接続文字列の解析"""
        if connection_string.startswith('postgresql://') or connection_string.startswith('postgres://'):
            parsed = urlparse(connection_string)
            return {
                'type': 'postgresql',
                'host': parsed.hostname,
                'port': parsed.port or 5432,
                'database': parsed.path.lstrip('/'),
                'username': parsed.username,
                'password': parsed.password
            }
        elif connection_string.startswith('mysql://'):
            parsed = urlparse(connection_string)
            return {
                'type': 'mysql',
                'host': parsed.hostname,
                'port': parsed.port or 3306,
                'database': parsed.path.lstrip('/'),
                'username': parsed.username,
                'password': parsed.password
            }
        else:
            # SQLite
            return {
                'type': 'sqlite',
                'path': connection_string.replace('sqlite:///', '')
            }
    
    def _get_db_path(self) -> str:
        """データベースパスの取得"""
        if self.db_type == 'sqlite':
            return self.db_config.get('path', ':memory:')
        else:
            return self.connection_string
    
    def _init_connection_pool(self):
        """接続プールの初期化"""
        try:
            if self.db_type == 'postgresql':
                self._init_postgresql_pool()
            elif self.db_type == 'mysql':
                self._init_mysql_pool()
            else:
                # SQLiteは接続プールを使用しない
                self.logger.info("SQLite detected, connection pooling disabled")
                
        except Exception as e:
            self.logger.error(f"Connection pool initialization failed: {e}")
            raise
    
    def _init_postgresql_pool(self):
        """PostgreSQL接続プールの初期化"""
        try:
            import psycopg2
            from psycopg2 import pool
            
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.pool_size,
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['username'],
                password=self.db_config['password'],
                connect_timeout=self.pool_timeout
            )
            
            self.logger.info(f"PostgreSQL connection pool initialized (size: {self.pool_size})")
            
        except ImportError:
            self.logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            raise
        except Exception as e:
            self.logger.error(f"PostgreSQL connection pool initialization failed: {e}")
            raise
    
    def _init_mysql_pool(self):
        """MySQL接続プールの初期化"""
        try:
            import mysql.connector.pooling
            
            pool_config = {
                'pool_name': 'tou_connect_pool',
                'pool_size': self.pool_size,
                'pool_reset_session': True,
                'host': self.db_config['host'],
                'port': self.db_config['port'],
                'database': self.db_config['database'],
                'user': self.db_config['username'],
                'password': self.db_config['password'],
                'connect_timeout': self.pool_timeout
            }
            
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)
            self.logger.info(f"MySQL connection pool initialized (size: {self.pool_size})")
            
        except ImportError:
            self.logger.error("mysql-connector-python not installed. Install with: pip install mysql-connector-python")
            raise
        except Exception as e:
            self.logger.error(f"MySQL connection pool initialization failed: {e}")
            raise
    
    def get_connection(self):
        """接続プールから接続を取得"""
        if not self.connection_pool:
            # SQLiteの場合は親クラスの接続を使用
            return super().get_connection()
        
        try:
            if self.db_type == 'postgresql':
                return self.connection_pool.getconn()
            elif self.db_type == 'mysql':
                return self.connection_pool.get_connection()
        except Exception as e:
            self.stats['connection_errors'] += 1
            self.logger.error(f"Failed to get connection from pool: {e}")
            raise
    
    def return_connection(self, connection):
        """接続をプールに返却"""
        if not self.connection_pool:
            # SQLiteの場合は親クラスの処理
            if connection:
                connection.close()
            return
        
        try:
            if self.db_type == 'postgresql':
                self.connection_pool.putconn(connection)
            elif self.db_type == 'mysql':
                connection.close()  # MySQL connector handles pool return automatically
        except Exception as e:
            self.logger.error(f"Failed to return connection to pool: {e}")
    
    def execute_with_retry(self, query: str, params: tuple = None, max_retries: int = 3) -> Any:
        """リトライ機能付きクエリ実行"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                self.stats['total_queries'] += 1
                
                if self.db_type == 'sqlite':
                    # SQLiteの場合は親クラスのメソッドを使用
                    if params is None:
                        return super().execute_query(query)
                    else:
                        return super().execute_query(query, params)
                else:
                    # PostgreSQL/MySQLの場合
                    return self._execute_pooled_query(query, params)
                    
            except Exception as e:
                last_exception = e
                self.stats['failed_queries'] += 1
                
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 0.1  # Exponential backoff
                    self.logger.warning(f"Query failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Query failed after {max_retries} attempts: {e}")
        
        raise last_exception
    
    def _execute_pooled_query(self, query: str, params: tuple = None) -> Any:
        """接続プールを使用したクエリ実行"""
        connection = None
        cursor = None
        
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # SELECT文の場合は結果を取得
            if query.strip().upper().startswith('SELECT'):
                if self.db_type == 'postgresql':
                    columns = [desc[0] for desc in cursor.description]
                    results = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in results]
                elif self.db_type == 'mysql':
                    columns = [desc[0] for desc in cursor.description]
                    results = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in results]
            else:
                # INSERT/UPDATE/DELETE文の場合
                connection.commit()
                return cursor.rowcount
                
        except Exception as e:
            if connection:
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.return_connection(connection)
    
    def fetch_one_with_retry(self, query: str, params: tuple = None) -> Optional[Dict]:
        """リトライ機能付き単一レコード取得"""
        results = self.execute_with_retry(query, params)
        if isinstance(results, list) and results:
            return results[0]
        return None
    
    def fetch_all_with_retry(self, query: str, params: tuple = None) -> List[Dict]:
        """リトライ機能付き全レコード取得"""
        results = self.execute_with_retry(query, params)
        if isinstance(results, list):
            return results
        return []
    
    def create_backup(self, backup_type: str = 'full') -> str:
        """データベースバックアップの作成"""
        try:
            backup_id = self.backup_manager.create_backup(backup_type)
            self.stats['last_backup'] = datetime.now(timezone.utc).isoformat()
            self.logger.info(f"Backup created successfully: {backup_id}")
            return backup_id
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            raise
    
    def restore_from_backup(self, backup_id: str) -> bool:
        """バックアップからの復元"""
        try:
            success = self.backup_manager.restore_backup(backup_id)
            if success:
                self.logger.info(f"Database restored from backup: {backup_id}")
            else:
                self.logger.error(f"Database restore failed: {backup_id}")
            return success
        except Exception as e:
            self.logger.error(f"Database restore error: {e}")
            return False
    
    def get_connection_pool_stats(self) -> Dict[str, Any]:
        """接続プール統計情報の取得"""
        if not self.connection_pool:
            return {'type': 'sqlite', 'pool_enabled': False}
        
        try:
            if self.db_type == 'postgresql':
                return {
                    'type': 'postgresql',
                    'pool_enabled': True,
                    'pool_size': self.pool_size,
                    'connections_in_use': len(self.connection_pool._used),
                    'connections_available': len(self.connection_pool._pool)
                }
            elif self.db_type == 'mysql':
                return {
                    'type': 'mysql',
                    'pool_enabled': True,
                    'pool_size': self.pool_size,
                    'pool_name': self.connection_pool.pool_name
                }
        except Exception as e:
            self.logger.error(f"Failed to get pool stats: {e}")
            
        return {'type': self.db_type, 'pool_enabled': True, 'error': 'stats_unavailable'}
    
    def get_database_stats(self) -> Dict[str, Any]:
        """データベース統計情報の取得"""
        stats = self.stats.copy()
        stats['uptime_seconds'] = time.time() - stats['uptime_start']
        stats['connection_pool'] = self.get_connection_pool_stats()
        stats['database_type'] = self.db_type
        
        # テーブル統計
        try:
            if self.db_type == 'postgresql':
                table_stats = self._get_postgresql_table_stats()
            elif self.db_type == 'mysql':
                table_stats = self._get_mysql_table_stats()
            else:
                table_stats = self._get_sqlite_table_stats()
            
            stats['tables'] = table_stats
        except Exception as e:
            self.logger.error(f"Failed to get table stats: {e}")
            stats['tables'] = {'error': str(e)}
        
        return stats
    
    def _get_postgresql_table_stats(self) -> Dict[str, Any]:
        """PostgreSQLテーブル統計"""
        query = """
        SELECT 
            schemaname,
            tablename,
            n_tup_ins as inserts,
            n_tup_upd as updates,
            n_tup_del as deletes,
            n_live_tup as live_tuples,
            n_dead_tup as dead_tuples
        FROM pg_stat_user_tables
        ORDER BY n_live_tup DESC
        """
        
        try:
            results = self.fetch_all_with_retry(query)
            return {'tables': results, 'total_tables': len(results)}
        except Exception as e:
            return {'error': str(e)}
    
    def _get_mysql_table_stats(self) -> Dict[str, Any]:
        """MySQLテーブル統計"""
        query = """
        SELECT 
            table_name,
            table_rows,
            data_length,
            index_length,
            (data_length + index_length) as total_size
        FROM information_schema.tables 
        WHERE table_schema = DATABASE()
        ORDER BY table_rows DESC
        """
        
        try:
            results = self.fetch_all_with_retry(query)
            return {'tables': results, 'total_tables': len(results)}
        except Exception as e:
            return {'error': str(e)}
    
    def _get_sqlite_table_stats(self) -> Dict[str, Any]:
        """SQLiteテーブル統計"""
        try:
            # テーブル一覧取得
            tables_query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """
            tables = self.fetch_all_with_retry(tables_query)
            
            table_stats = []
            for table in tables:
                table_name = table['name']
                count_query = f"SELECT COUNT(*) as count FROM {table_name}"
                count_result = self.fetch_one_with_retry(count_query)
                table_stats.append({
                    'table_name': table_name,
                    'row_count': count_result['count'] if count_result else 0
                })
            
            return {'tables': table_stats, 'total_tables': len(table_stats)}
        except Exception as e:
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """データベースヘルスチェック"""
        start_time = time.time()
        
        try:
            # 簡単なクエリでDB接続を確認
            test_query = "SELECT 1 as test"
            result = self.fetch_one_with_retry(test_query)
            
            response_time = (time.time() - start_time) * 1000
            
            if result and result.get('test') == 1:
                return {
                    'status': 'healthy',
                    'response_time_ms': round(response_time, 2),
                    'database_type': self.db_type,
                    'connection_pool': self.get_connection_pool_stats(),
                    'statistics': self.get_database_stats()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'Test query returned unexpected result',
                    'response_time_ms': round(response_time, 2)
                }
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time_ms': round(response_time, 2)
            }
    
    def close_all_connections(self):
        """全接続のクローズ"""
        try:
            if self.connection_pool:
                if self.db_type == 'postgresql':
                    self.connection_pool.closeall()
                elif self.db_type == 'mysql':
                    # MySQL connector handles this automatically
                    pass
                
                self.logger.info("All database connections closed")
        except Exception as e:
            self.logger.error(f"Error closing connections: {e}")


class BackupManager:
    """データベースバックアップ管理クラス"""
    
    def __init__(self, db_manager: ProductionDatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # バックアップ設定
        self.backup_dir = os.getenv('BACKUP_DIR', 'backups')
        self.max_backups = int(os.getenv('MAX_BACKUPS', '30'))
        
        # バックアップディレクトリの作成
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, backup_type: str = 'full') -> str:
        """バックアップの作成"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        backup_id = f"{backup_type}_{timestamp}"
        
        try:
            if self.db_manager.db_type == 'postgresql':
                return self._create_postgresql_backup(backup_id)
            elif self.db_manager.db_type == 'mysql':
                return self._create_mysql_backup(backup_id)
            else:
                return self._create_sqlite_backup(backup_id)
                
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            raise
    
    def _create_postgresql_backup(self, backup_id: str) -> str:
        """PostgreSQLバックアップの作成"""
        import subprocess
        
        config = self.db_manager.db_config
        backup_file = os.path.join(self.backup_dir, f"{backup_id}.sql")
        
        # pg_dumpコマンドの実行
        cmd = [
            'pg_dump',
            f"--host={config['host']}",
            f"--port={config['port']}",
            f"--username={config['username']}",
            f"--dbname={config['database']}",
            '--no-password',
            '--verbose',
            '--clean',
            '--no-acl',
            '--no-owner',
            f"--file={backup_file}"
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = config['password']
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            self.logger.info(f"PostgreSQL backup created: {backup_file}")
            return backup_id
        else:
            raise Exception(f"pg_dump failed: {result.stderr}")
    
    def _create_mysql_backup(self, backup_id: str) -> str:
        """MySQLバックアップの作成"""
        import subprocess
        
        config = self.db_manager.db_config
        backup_file = os.path.join(self.backup_dir, f"{backup_id}.sql")
        
        # mysqldumpコマンドの実行
        cmd = [
            'mysqldump',
            f"--host={config['host']}",
            f"--port={config['port']}",
            f"--user={config['username']}",
            f"--password={config['password']}",
            '--single-transaction',
            '--routines',
            '--triggers',
            config['database']
        ]
        
        with open(backup_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            self.logger.info(f"MySQL backup created: {backup_file}")
            return backup_id
        else:
            raise Exception(f"mysqldump failed: {result.stderr}")
    
    def _create_sqlite_backup(self, backup_id: str) -> str:
        """SQLiteバックアップの作成"""
        import shutil
        
        source_file = self.db_manager.db_config.get('path')
        if source_file == ':memory:':
            raise Exception("Cannot backup in-memory database")
        
        backup_file = os.path.join(self.backup_dir, f"{backup_id}.db")
        shutil.copy2(source_file, backup_file)
        
        self.logger.info(f"SQLite backup created: {backup_file}")
        return backup_id
    
    def restore_backup(self, backup_id: str) -> bool:
        """バックアップからの復元"""
        try:
            if self.db_manager.db_type == 'postgresql':
                return self._restore_postgresql_backup(backup_id)
            elif self.db_manager.db_type == 'mysql':
                return self._restore_mysql_backup(backup_id)
            else:
                return self._restore_sqlite_backup(backup_id)
                
        except Exception as e:
            self.logger.error(f"Backup restore failed: {e}")
            return False
    
    def _restore_postgresql_backup(self, backup_id: str) -> bool:
        """PostgreSQLバックアップの復元"""
        import subprocess
        
        config = self.db_manager.db_config
        backup_file = os.path.join(self.backup_dir, f"{backup_id}.sql")
        
        if not os.path.exists(backup_file):
            raise Exception(f"Backup file not found: {backup_file}")
        
        # psqlコマンドの実行
        cmd = [
            'psql',
            f"--host={config['host']}",
            f"--port={config['port']}",
            f"--username={config['username']}",
            f"--dbname={config['database']}",
            '--no-password',
            f"--file={backup_file}"
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = config['password']
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            self.logger.info(f"PostgreSQL backup restored: {backup_id}")
            return True
        else:
            raise Exception(f"psql restore failed: {result.stderr}")
    
    def _restore_mysql_backup(self, backup_id: str) -> bool:
        """MySQLバックアップの復元"""
        import subprocess
        
        config = self.db_manager.db_config
        backup_file = os.path.join(self.backup_dir, f"{backup_id}.sql")
        
        if not os.path.exists(backup_file):
            raise Exception(f"Backup file not found: {backup_file}")
        
        # mysqlコマンドの実行
        cmd = [
            'mysql',
            f"--host={config['host']}",
            f"--port={config['port']}",
            f"--user={config['username']}",
            f"--password={config['password']}",
            config['database']
        ]
        
        with open(backup_file, 'r') as f:
            result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            self.logger.info(f"MySQL backup restored: {backup_id}")
            return True
        else:
            raise Exception(f"mysql restore failed: {result.stderr}")
    
    def _restore_sqlite_backup(self, backup_id: str) -> bool:
        """SQLiteバックアップの復元"""
        import shutil
        
        backup_file = os.path.join(self.backup_dir, f"{backup_id}.db")
        target_file = self.db_manager.db_config.get('path')
        
        if not os.path.exists(backup_file):
            raise Exception(f"Backup file not found: {backup_file}")
        
        if target_file == ':memory:':
            raise Exception("Cannot restore to in-memory database")
        
        shutil.copy2(backup_file, target_file)
        self.logger.info(f"SQLite backup restored: {backup_id}")
        return True
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """バックアップ一覧の取得"""
        backups = []
        
        try:
            for filename in os.listdir(self.backup_dir):
                if filename.endswith(('.sql', '.db')):
                    filepath = os.path.join(self.backup_dir, filename)
                    stat = os.stat(filepath)
                    
                    backups.append({
                        'backup_id': filename.rsplit('.', 1)[0],
                        'filename': filename,
                        'size_bytes': stat.st_size,
                        'created_at': datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                        'modified_at': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                    })
            
            # 作成日時でソート（新しい順）
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to list backups: {e}")
        
        return backups
    
    def cleanup_old_backups(self):
        """古いバックアップのクリーンアップ"""
        try:
            backups = self.list_backups()
            
            if len(backups) > self.max_backups:
                # 古いバックアップを削除
                backups_to_delete = backups[self.max_backups:]
                
                for backup in backups_to_delete:
                    backup_file = os.path.join(self.backup_dir, backup['filename'])
                    os.remove(backup_file)
                    self.logger.info(f"Deleted old backup: {backup['filename']}")
                
                self.logger.info(f"Cleaned up {len(backups_to_delete)} old backups")
                
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {e}")