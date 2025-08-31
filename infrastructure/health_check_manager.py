"""
HealthCheckManager - システム健全性監視クラス
データベース、外部API、キャッシュの状態を監視し、ヘルスチェック情報を提供
"""
import os
import time
import logging
import psutil
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from database.database_manager import DatabaseManager


class HealthCheckManager:
    """システム健全性監視クラス"""
    
    def __init__(self, db_manager: DatabaseManager, security_manager=None):
        self.db = db_manager
        self.security_manager = security_manager
        self.logger = logging.getLogger(__name__)
        
        # ヘルスチェック設定
        self.check_timeout = 5.0  # 5秒でタイムアウト
        self.critical_thresholds = {
            'cpu_percent': 90.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'response_time_ms': 3000
        }
    
    def get_comprehensive_health_status(self) -> Dict[str, Any]:
        """包括的なヘルスチェック実行"""
        start_time = time.time()
        
        health_status = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'healthy',
            'version': '1.0.0',
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'checks': {},
            'metrics': {},
            'response_time_ms': 0
        }
        
        try:
            # 各種チェック実行
            checks = [
                ('database', self.check_database_connection),
                ('external_apis', self.check_external_apis),
                ('cache', self.check_cache_status),
                ('system_resources', self.check_system_resources),
                ('disk_space', self.check_disk_space)
            ]
            
            overall_status = 'healthy'
            
            for check_name, check_func in checks:
                try:
                    check_result = check_func()
                    health_status['checks'][check_name] = check_result
                    
                    # 全体ステータスの更新
                    if check_result['status'] == 'unhealthy':
                        overall_status = 'unhealthy'
                    elif check_result['status'] == 'degraded' and overall_status == 'healthy':
                        overall_status = 'degraded'
                        
                except Exception as e:
                    self.logger.error(f"Health check {check_name} failed: {e}")
                    health_status['checks'][check_name] = {
                        'status': 'unhealthy',
                        'error': str(e),
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    overall_status = 'unhealthy'
            
            # システムメトリクス取得
            health_status['metrics'] = self.get_system_metrics()
            
            # 全体ステータス設定
            health_status['status'] = overall_status
            
            # レスポンス時間計算
            response_time = (time.time() - start_time) * 1000
            health_status['response_time_ms'] = round(response_time, 2)
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Comprehensive health check failed: {e}")
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'unhealthy',
                'error': str(e),
                'response_time_ms': round((time.time() - start_time) * 1000, 2)
            }
    
    def check_database_connection(self) -> Dict[str, Any]:
        """データベース接続チェック"""
        start_time = time.time()
        
        try:
            # 簡単なクエリでDB接続を確認
            test_query = "SELECT 1 as test"
            result = self.db.fetch_one(test_query)
            
            response_time = (time.time() - start_time) * 1000
            
            if result and result.get('test') == 1:
                # 追加のDB統計情報取得
                db_stats = self._get_database_statistics()
                
                return {
                    'status': 'healthy',
                    'response_time_ms': round(response_time, 2),
                    'connection_pool': 'active',
                    'statistics': db_stats,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'Database query returned unexpected result',
                    'response_time_ms': round(response_time, 2),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"Database health check failed: {e}")
            
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time_ms': round(response_time, 2),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def check_external_apis(self) -> Dict[str, Any]:
        """外部API接続チェック"""
        api_status = {
            'status': 'healthy',
            'apis': {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # テスト環境では外部APIチェックをスキップ
        if os.getenv('ENVIRONMENT') == 'testing':
            api_status['apis']['gemini'] = {'status': 'skipped', 'reason': 'testing environment'}
            api_status['apis']['twitter'] = {'status': 'skipped', 'reason': 'testing environment'}
            return api_status
        
        try:
            # Gemini APIキーチェック
            if self.security_manager:
                gemini_key = self.security_manager.get_api_key('gemini')
                if gemini_key and len(gemini_key) > 10:
                    api_status['apis']['gemini'] = {
                        'status': 'healthy',
                        'key_configured': True
                    }
                else:
                    api_status['apis']['gemini'] = {
                        'status': 'degraded',
                        'key_configured': False,
                        'warning': 'API key not properly configured'
                    }
                    api_status['status'] = 'degraded'
                
                # Twitter APIキーチェック
                twitter_key = self.security_manager.get_api_key('twitter')
                if twitter_key and len(twitter_key) > 10:
                    api_status['apis']['twitter'] = {
                        'status': 'healthy',
                        'key_configured': True
                    }
                else:
                    api_status['apis']['twitter'] = {
                        'status': 'degraded',
                        'key_configured': False,
                        'warning': 'API key not properly configured'
                    }
                    api_status['status'] = 'degraded'
            else:
                api_status['status'] = 'degraded'
                api_status['warning'] = 'Security manager not available'
            
            return api_status
            
        except Exception as e:
            self.logger.error(f"External API health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def check_cache_status(self) -> Dict[str, Any]:
        """キャッシュ状態チェック"""
        try:
            redis_url = os.getenv('REDIS_URL')
            
            if not redis_url:
                return {
                    'status': 'degraded',
                    'type': 'memory',
                    'warning': 'Redis not configured, using memory cache',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            # Redis接続テスト（実装時）
            try:
                import redis
                r = redis.from_url(redis_url)
                r.ping()
                
                # Redis統計情報取得
                info = r.info()
                
                return {
                    'status': 'healthy',
                    'type': 'redis',
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_human': info.get('used_memory_human', 'unknown'),
                    'uptime_in_seconds': info.get('uptime_in_seconds', 0),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
            except ImportError:
                return {
                    'status': 'degraded',
                    'type': 'memory',
                    'warning': 'Redis client not installed',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            except Exception as redis_error:
                return {
                    'status': 'unhealthy',
                    'type': 'redis',
                    'error': str(redis_error),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Cache health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """システムリソースチェック"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # メモリ使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # システム負荷
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
            
            # ステータス判定
            status = 'healthy'
            warnings = []
            
            if cpu_percent > self.critical_thresholds['cpu_percent']:
                status = 'degraded'
                warnings.append(f'High CPU usage: {cpu_percent}%')
            
            if memory_percent > self.critical_thresholds['memory_percent']:
                status = 'degraded'
                warnings.append(f'High memory usage: {memory_percent}%')
            
            return {
                'status': status,
                'cpu_percent': round(cpu_percent, 2),
                'memory_percent': round(memory_percent, 2),
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'load_average': {
                    '1min': round(load_avg[0], 2),
                    '5min': round(load_avg[1], 2),
                    '15min': round(load_avg[2], 2)
                },
                'warnings': warnings,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"System resources check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def check_disk_space(self) -> Dict[str, Any]:
        """ディスク容量チェック"""
        try:
            disk_usage = psutil.disk_usage('/')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            
            status = 'healthy'
            if disk_percent > self.critical_thresholds['disk_percent']:
                status = 'degraded'
            
            return {
                'status': status,
                'disk_percent': round(disk_percent, 2),
                'total_gb': round(disk_usage.total / (1024**3), 2),
                'used_gb': round(disk_usage.used / (1024**3), 2),
                'free_gb': round(disk_usage.free / (1024**3), 2),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Disk space check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクス取得"""
        try:
            return {
                'uptime_seconds': time.time() - psutil.boot_time(),
                'process_count': len(psutil.pids()),
                'network_connections': len(psutil.net_connections()),
                'python_version': f"{psutil.version_info.major}.{psutil.version_info.minor}",
                'platform': psutil.LINUX if hasattr(psutil, 'LINUX') else 'unknown'
            }
        except Exception as e:
            self.logger.error(f"System metrics collection failed: {e}")
            return {'error': str(e)}
    
    def _get_database_statistics(self) -> Dict[str, Any]:
        """データベース統計情報取得"""
        try:
            stats = {}
            
            # テーブル数取得
            tables_query = """
            SELECT COUNT(*) as table_count 
            FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """
            result = self.db.fetch_one(tables_query)
            if result:
                stats['table_count'] = result['table_count']
            
            # 主要テーブルのレコード数
            main_tables = ['users', 'user_analyses', 'user_consents', 'audit_logs']
            for table in main_tables:
                try:
                    count_query = f"SELECT COUNT(*) as count FROM {table}"
                    result = self.db.fetch_one(count_query)
                    if result:
                        stats[f'{table}_count'] = result['count']
                except:
                    stats[f'{table}_count'] = 'N/A'
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Database statistics collection failed: {e}")
            return {'error': str(e)}
    
    def is_healthy(self) -> bool:
        """システムが健全かどうかの簡易チェック"""
        try:
            health_status = self.get_comprehensive_health_status()
            return health_status['status'] in ['healthy', 'degraded']
        except:
            return False
    
    def get_readiness_status(self) -> Dict[str, Any]:
        """Kubernetesスタイルのreadiness probe"""
        try:
            # 最低限の機能チェック
            db_check = self.check_database_connection()
            
            if db_check['status'] == 'healthy':
                return {
                    'status': 'ready',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    'status': 'not_ready',
                    'reason': 'Database not available',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'not_ready',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_liveness_status(self) -> Dict[str, Any]:
        """Kubernetesスタイルのliveness probe"""
        try:
            # アプリケーションが生きているかの基本チェック
            return {
                'status': 'alive',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'uptime_seconds': time.time() - psutil.boot_time()
            }
        except Exception as e:
            return {
                'status': 'dead',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }