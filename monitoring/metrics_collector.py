"""
MetricsCollector - メトリクス収集システム
アプリケーション、システム、ビジネスメトリクスの収集と集約
"""
import os
import time
import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from monitoring.monitoring_manager import MonitoringManager, MetricType


class MetricsCollector:
    """メトリクス収集クラス"""
    
    def __init__(self, monitoring_manager: MonitoringManager, db_manager=None):
        self.monitoring = monitoring_manager
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        
        # 収集間隔（秒）
        self.collection_intervals = {
            'system': 30,      # システムメトリクス
            'application': 60, # アプリケーションメトリクス
            'business': 300    # ビジネスメトリクス
        }
        
        # 収集スレッド
        self.collection_threads = {}
        self.running = False
        
        # カスタムメトリクス収集関数
        self.custom_collectors = {}
        
        # 初期化
        self._init_collectors()
    
    def _init_collectors(self):
        """コレクターの初期化"""
        try:
            # デフォルトコレクターの登録
            self.register_collector('system', self._collect_system_metrics)
            self.register_collector('application', self._collect_application_metrics)
            self.register_collector('business', self._collect_business_metrics)
            
            self.logger.info("Metrics collectors initialized")
            
        except Exception as e:
            self.logger.error(f"Metrics collector initialization failed: {e}")
            raise
    
    def register_collector(self, name: str, collector_func, interval: int = 60):
        """カスタムコレクターの登録"""
        self.custom_collectors[name] = collector_func
        self.collection_intervals[name] = interval
        
        self.logger.info(f"Registered custom collector: {name} (interval: {interval}s)")
    
    def start_collection(self):
        """メトリクス収集の開始"""
        if self.running:
            return
        
        self.running = True
        
        for collector_name, collector_func in self.custom_collectors.items():
            interval = self.collection_intervals.get(collector_name, 60)
            
            thread = threading.Thread(
                target=self._collection_worker,
                args=(collector_name, collector_func, interval),
                daemon=True
            )
            
            self.collection_threads[collector_name] = thread
            thread.start()
            
            self.logger.info(f"Started metrics collection: {collector_name}")
        
        self.logger.info("All metrics collectors started")
    
    def stop_collection(self):
        """メトリクス収集の停止"""
        self.running = False
        
        for thread in self.collection_threads.values():
            thread.join(timeout=5)
        
        self.collection_threads.clear()
        self.logger.info("All metrics collectors stopped")
    
    def _collection_worker(self, name: str, collector_func, interval: int):
        """メトリクス収集ワーカー"""
        while self.running:
            try:
                start_time = time.time()
                
                # メトリクス収集実行
                collector_func()
                
                # 収集時間の記録
                collection_time = (time.time() - start_time) * 1000
                self.monitoring.record_timer(
                    f"metrics.collection.{name}",
                    collection_time,
                    {'collector': name}
                )
                
                # 次の収集まで待機
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Metrics collection error ({name}): {e}")
                time.sleep(interval)  # エラー時も間隔を保つ
    
    def _collect_system_metrics(self):
        """システムメトリクスの収集"""
        try:
            import psutil
            
            # CPU メトリクス
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
            
            self.monitoring.record_gauge("system.cpu.usage_percent", cpu_percent, unit="%")
            self.monitoring.record_gauge("system.cpu.count", cpu_count)
            self.monitoring.record_gauge("system.cpu.load_1min", load_avg[0])
            self.monitoring.record_gauge("system.cpu.load_5min", load_avg[1])
            self.monitoring.record_gauge("system.cpu.load_15min", load_avg[2])
            
            # メモリメトリクス
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            self.monitoring.record_gauge("system.memory.total_gb", memory.total / (1024**3), unit="GB")
            self.monitoring.record_gauge("system.memory.available_gb", memory.available / (1024**3), unit="GB")
            self.monitoring.record_gauge("system.memory.used_gb", memory.used / (1024**3), unit="GB")
            self.monitoring.record_gauge("system.memory.usage_percent", memory.percent, unit="%")
            
            # macOSではcachedが利用できない場合がある
            if hasattr(memory, 'cached'):
                self.monitoring.record_gauge("system.memory.cached_gb", memory.cached / (1024**3), unit="GB")
            
            self.monitoring.record_gauge("system.swap.total_gb", swap.total / (1024**3), unit="GB")
            self.monitoring.record_gauge("system.swap.used_gb", swap.used / (1024**3), unit="GB")
            self.monitoring.record_gauge("system.swap.usage_percent", swap.percent, unit="%")
            
            # ディスクメトリクス
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            self.monitoring.record_gauge("system.disk.total_gb", disk_usage.total / (1024**3), unit="GB")
            self.monitoring.record_gauge("system.disk.used_gb", disk_usage.used / (1024**3), unit="GB")
            self.monitoring.record_gauge("system.disk.free_gb", disk_usage.free / (1024**3), unit="GB")
            self.monitoring.record_gauge("system.disk.usage_percent", 
                                       (disk_usage.used / disk_usage.total) * 100, unit="%")
            
            if disk_io:
                self.monitoring.record_counter("system.disk.read_bytes", disk_io.read_bytes)
                self.monitoring.record_counter("system.disk.write_bytes", disk_io.write_bytes)
                self.monitoring.record_counter("system.disk.read_count", disk_io.read_count)
                self.monitoring.record_counter("system.disk.write_count", disk_io.write_count)
            
            # ネットワークメトリクス
            net_io = psutil.net_io_counters()
            net_connections = len(psutil.net_connections())
            
            if net_io:
                self.monitoring.record_counter("system.network.bytes_sent", net_io.bytes_sent)
                self.monitoring.record_counter("system.network.bytes_recv", net_io.bytes_recv)
                self.monitoring.record_counter("system.network.packets_sent", net_io.packets_sent)
                self.monitoring.record_counter("system.network.packets_recv", net_io.packets_recv)
                self.monitoring.record_counter("system.network.errors_in", net_io.errin)
                self.monitoring.record_counter("system.network.errors_out", net_io.errout)
            
            self.monitoring.record_gauge("system.network.connections", net_connections)
            
            # プロセスメトリクス
            process_count = len(psutil.pids())
            self.monitoring.record_gauge("system.processes.count", process_count)
            
        except Exception as e:
            self.logger.error(f"System metrics collection failed: {e}")
    
    def _collect_application_metrics(self):
        """アプリケーションメトリクスの収集"""
        try:
            # データベースメトリクス
            if self.db:
                self._collect_database_metrics()
            
            # Pythonプロセスメトリクス
            self._collect_python_metrics()
            
            # Flask アプリケーションメトリクス
            self._collect_flask_metrics()
            
        except Exception as e:
            self.logger.error(f"Application metrics collection failed: {e}")
    
    def _collect_database_metrics(self):
        """データベースメトリクスの収集"""
        try:
            # データベース統計の取得
            if hasattr(self.db, 'get_database_stats'):
                stats = self.db.get_database_stats()
                
                # 基本統計
                self.monitoring.record_counter("database.queries.total", stats.get('total_queries', 0))
                self.monitoring.record_counter("database.queries.failed", stats.get('failed_queries', 0))
                self.monitoring.record_counter("database.connections.errors", stats.get('connection_errors', 0))
                
                # 接続プール統計
                pool_stats = stats.get('connection_pool', {})
                if pool_stats.get('pool_enabled'):
                    self.monitoring.record_gauge("database.pool.size", pool_stats.get('pool_size', 0))
                    self.monitoring.record_gauge("database.pool.connections_in_use", 
                                               pool_stats.get('connections_in_use', 0))
                    self.monitoring.record_gauge("database.pool.connections_available", 
                                               pool_stats.get('connections_available', 0))
                
                # テーブル統計
                tables = stats.get('tables', {})
                if isinstance(tables, dict) and 'tables' in tables:
                    total_tables = tables.get('total_tables', 0)
                    self.monitoring.record_gauge("database.tables.count", total_tables)
            
            # データベースヘルスチェック
            if hasattr(self.db, 'health_check'):
                start_time = time.time()
                health = self.db.health_check()
                response_time = (time.time() - start_time) * 1000
                
                self.monitoring.record_timer("database.health_check.response_time", response_time)
                self.monitoring.record_gauge("database.health_check.status", 
                                           1 if health.get('status') == 'healthy' else 0)
            
        except Exception as e:
            self.logger.error(f"Database metrics collection failed: {e}")
    
    def _collect_python_metrics(self):
        """Pythonプロセスメトリクスの収集"""
        try:
            import psutil
            import gc
            import sys
            
            # 現在のプロセス
            process = psutil.Process()
            
            # メモリ使用量
            memory_info = process.memory_info()
            self.monitoring.record_gauge("python.memory.rss_mb", memory_info.rss / (1024**2), unit="MB")
            self.monitoring.record_gauge("python.memory.vms_mb", memory_info.vms / (1024**2), unit="MB")
            
            # CPU使用率
            cpu_percent = process.cpu_percent()
            self.monitoring.record_gauge("python.cpu.usage_percent", cpu_percent, unit="%")
            
            # スレッド数
            thread_count = process.num_threads()
            self.monitoring.record_gauge("python.threads.count", thread_count)
            
            # ファイルディスクリプタ
            try:
                fd_count = process.num_fds()
                self.monitoring.record_gauge("python.file_descriptors.count", fd_count)
            except AttributeError:
                pass  # Windowsでは利用不可
            
            # ガベージコレクション
            gc_stats = gc.get_stats()
            for i, stat in enumerate(gc_stats):
                self.monitoring.record_counter(f"python.gc.generation_{i}.collections", stat['collections'])
                self.monitoring.record_counter(f"python.gc.generation_{i}.collected", stat['collected'])
                self.monitoring.record_counter(f"python.gc.generation_{i}.uncollectable", stat['uncollectable'])
            
            # オブジェクト数
            object_count = len(gc.get_objects())
            self.monitoring.record_gauge("python.objects.count", object_count)
            
        except Exception as e:
            self.logger.error(f"Python metrics collection failed: {e}")
    
    def _collect_flask_metrics(self):
        """Flaskアプリケーションメトリクスの収集"""
        try:
            # パフォーマンス統計から Flask メトリクスを収集
            perf_stats = self.monitoring.get_performance_stats(hours=1)
            
            for operation, stats in perf_stats.items():
                if operation.startswith('api_'):
                    # API エンドポイントのメトリクス
                    endpoint = operation.replace('api_', '')
                    
                    self.monitoring.record_gauge(f"flask.endpoint.{endpoint}.requests_per_hour", 
                                               stats['total_requests'])
                    self.monitoring.record_gauge(f"flask.endpoint.{endpoint}.error_rate", 
                                               stats['error_rate'], unit="%")
                    self.monitoring.record_gauge(f"flask.endpoint.{endpoint}.avg_response_time", 
                                               stats['avg_duration_ms'], unit="ms")
                    self.monitoring.record_gauge(f"flask.endpoint.{endpoint}.p95_response_time", 
                                               stats['p95_duration_ms'], unit="ms")
            
        except Exception as e:
            self.logger.error(f"Flask metrics collection failed: {e}")
    
    def _collect_business_metrics(self):
        """ビジネスメトリクスの収集"""
        try:
            if not self.db:
                return
            
            # ユーザー関連メトリクス
            self._collect_user_metrics()
            
            # 分析関連メトリクス
            self._collect_analysis_metrics()
            
            # マッチング関連メトリクス
            self._collect_matching_metrics()
            
            # 収益関連メトリクス
            self._collect_revenue_metrics()
            
        except Exception as e:
            self.logger.error(f"Business metrics collection failed: {e}")
    
    def _collect_user_metrics(self):
        """ユーザーメトリクスの収集"""
        try:
            # 総ユーザー数
            total_users_sql = "SELECT COUNT(*) as count FROM users WHERE is_active = TRUE"
            result = self._fetch_one_safe(total_users_sql)
            if result:
                self.monitoring.record_gauge("business.users.total", result['count'])
            
            # 新規ユーザー数（過去24時間）
            new_users_sql = """
            SELECT COUNT(*) as count FROM users 
            WHERE is_active = TRUE AND created_at > datetime('now', '-1 day')
            """
            result = self._fetch_one_safe(new_users_sql)
            if result:
                self.monitoring.record_gauge("business.users.new_24h", result['count'])
            
            # アクティブユーザー数（過去7日間）
            active_users_sql = """
            SELECT COUNT(DISTINCT user_id) as count FROM audit_logs 
            WHERE created_at > datetime('now', '-7 days')
            """
            result = self._fetch_one_safe(active_users_sql)
            if result:
                self.monitoring.record_gauge("business.users.active_7d", result['count'])
            
        except Exception as e:
            self.logger.error(f"User metrics collection failed: {e}")
    
    def _collect_analysis_metrics(self):
        """分析メトリクスの収集"""
        try:
            # 総分析数
            total_analyses_sql = "SELECT COUNT(*) as count FROM user_analyses"
            result = self._fetch_one_safe(total_analyses_sql)
            if result:
                self.monitoring.record_gauge("business.analyses.total", result['count'])
            
            # 新規分析数（過去24時間）
            new_analyses_sql = """
            SELECT COUNT(*) as count FROM user_analyses 
            WHERE created_at > datetime('now', '-1 day')
            """
            result = self._fetch_one_safe(new_analyses_sql)
            if result:
                self.monitoring.record_gauge("business.analyses.new_24h", result['count'])
            
            # 分析タイプ別統計
            analysis_types_sql = """
            SELECT analysis_type, COUNT(*) as count 
            FROM user_analyses 
            GROUP BY analysis_type
            """
            results = self._fetch_all_safe(analysis_types_sql)
            for result in results:
                analysis_type = result['analysis_type']
                count = result['count']
                self.monitoring.record_gauge(f"business.analyses.by_type.{analysis_type}", count)
            
        except Exception as e:
            self.logger.error(f"Analysis metrics collection failed: {e}")
    
    def _collect_matching_metrics(self):
        """マッチングメトリクスの収集"""
        try:
            # マッチング関連のメトリクスは、実際のマッチング実行時に記録される
            # ここでは統計的な情報を収集
            
            # 興味カテゴリ別統計
            interests_sql = """
            SELECT interest_category, COUNT(*) as count 
            FROM user_interests 
            GROUP BY interest_category
            """
            results = self._fetch_all_safe(interests_sql)
            for result in results:
                category = result['interest_category']
                count = result['count']
                self.monitoring.record_gauge(f"business.interests.{category}", count)
            
            # スキルカテゴリ別統計
            skills_sql = """
            SELECT skill_category, COUNT(*) as count 
            FROM user_skills 
            GROUP BY skill_category
            """
            results = self._fetch_all_safe(skills_sql)
            for result in results:
                category = result['skill_category']
                count = result['count']
                self.monitoring.record_gauge(f"business.skills.{category}", count)
            
        except Exception as e:
            self.logger.error(f"Matching metrics collection failed: {e}")
    
    def _collect_revenue_metrics(self):
        """収益メトリクスの収集"""
        try:
            # リソースクリック数
            total_clicks_sql = "SELECT COUNT(*) as count FROM resource_clicks"
            result = self._fetch_one_safe(total_clicks_sql)
            if result:
                self.monitoring.record_gauge("business.revenue.total_clicks", result['count'])
            
            # 新規クリック数（過去24時間）
            new_clicks_sql = """
            SELECT COUNT(*) as count FROM resource_clicks 
            WHERE clicked_at > datetime('now', '-1 day')
            """
            result = self._fetch_one_safe(new_clicks_sql)
            if result:
                self.monitoring.record_gauge("business.revenue.new_clicks_24h", result['count'])
            
            # コンバージョン数
            conversions_sql = """
            SELECT COUNT(*) as count FROM resource_clicks 
            WHERE conversion_tracked = TRUE
            """
            result = self._fetch_one_safe(conversions_sql)
            if result:
                self.monitoring.record_gauge("business.revenue.conversions", result['count'])
            
            # 収益額
            revenue_sql = """
            SELECT COALESCE(SUM(revenue_amount), 0) as total_revenue 
            FROM resource_clicks 
            WHERE revenue_amount IS NOT NULL
            """
            result = self._fetch_one_safe(revenue_sql)
            if result:
                self.monitoring.record_gauge("business.revenue.total_amount", 
                                           result['total_revenue'], unit="USD")
            
        except Exception as e:
            self.logger.error(f"Revenue metrics collection failed: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """メトリクス収集サマリーの取得"""
        try:
            return {
                'collectors_running': len([t for t in self.collection_threads.values() if t.is_alive()]),
                'total_collectors': len(self.custom_collectors),
                'collection_intervals': self.collection_intervals,
                'running': self.running,
                'registered_collectors': list(self.custom_collectors.keys())
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get metrics summary: {e}")
            return {'error': str(e)}
    
    def _fetch_one_safe(self, sql, params=None):
        """安全なfetch_one実行"""
        try:
            if hasattr(self.db, 'fetch_one_with_retry'):
                return self.db.fetch_one_with_retry(sql, params)
            elif hasattr(self.db, 'fetch_one'):
                return self.db.fetch_one(sql, params)
            else:
                # 基本的なSQLite実行
                cursor = self.db.connection.execute(sql, params or ())
                row = cursor.fetchone()
                if row:
                    # 辞書形式で返す
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            self.logger.error(f"Database fetch_one error: {e}")
            return None
    
    def _fetch_all_safe(self, sql, params=None):
        """安全なfetch_all実行"""
        try:
            if hasattr(self.db, 'fetch_all_with_retry'):
                return self.db.fetch_all_with_retry(sql, params)
            elif hasattr(self.db, 'fetch_all'):
                return self.db.fetch_all(sql, params)
            else:
                # 基本的なSQLite実行
                cursor = self.db.connection.execute(sql, params or ())
                rows = cursor.fetchall()
                if rows:
                    # 辞書形式で返す
                    columns = [description[0] for description in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
                return []
        except Exception as e:
            self.logger.error(f"Database fetch_all error: {e}")
            return []