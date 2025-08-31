"""
MonitoringManager - 監視・運用管理クラス
システムメトリクス収集、アラート送信、パフォーマンス追跡機能を提供
"""
import os
import json
import time
import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum


class AlertSeverity(Enum):
    """アラート重要度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MetricType(Enum):
    """メトリクスタイプ"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """メトリクスデータクラス"""
    name: str
    value: float
    metric_type: MetricType
    tags: Dict[str, str]
    timestamp: datetime
    unit: str = ""


@dataclass
class Alert:
    """アラートデータクラス"""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    source: str
    timestamp: datetime
    metadata: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class MonitoringManager:
    """監視・運用管理クラス"""
    
    def __init__(self, db_manager=None):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        
        # メトリクス保存
        self.metrics_buffer = deque(maxlen=10000)  # 最大10,000メトリクス
        self.metrics_lock = threading.Lock()
        
        # アラート管理
        self.alerts = {}
        self.alert_handlers = []
        self.alert_lock = threading.Lock()
        
        # パフォーマンス追跡
        self.performance_data = defaultdict(list)
        self.performance_lock = threading.Lock()
        
        # 閾値設定
        self.thresholds = {
            'response_time_ms': 3000,
            'error_rate_percent': 5.0,
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'database_response_ms': 1000
        }
        
        # 統計情報
        self.stats = {
            'total_metrics': 0,
            'total_alerts': 0,
            'active_alerts': 0,
            'start_time': time.time()
        }
        
        # バックグラウンドタスク
        self.background_thread = None
        self.running = False
        
        # 初期化
        self._init_monitoring()
    
    def _init_monitoring(self):
        """監視システムの初期化"""
        try:
            # デフォルトアラートハンドラーの追加
            self.add_alert_handler(self._default_alert_handler)
            
            # バックグラウンドタスクの開始
            self.start_background_tasks()
            
            self.logger.info("Monitoring system initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Monitoring initialization failed: {e}")
            raise
    
    def record_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE,
                     tags: Dict[str, str] = None, unit: str = ""):
        """メトリクスの記録"""
        try:
            metric = Metric(
                name=name,
                value=value,
                metric_type=metric_type,
                tags=tags or {},
                timestamp=datetime.now(timezone.utc),
                unit=unit
            )
            
            with self.metrics_lock:
                self.metrics_buffer.append(metric)
                self.stats['total_metrics'] += 1
            
            # データベースに保存（非同期）
            if self.db:
                self._save_metric_to_db(metric)
            
            # 閾値チェック
            self._check_thresholds(metric)
            
        except Exception as e:
            self.logger.error(f"Failed to record metric {name}: {e}")
    
    def record_counter(self, name: str, value: float = 1, tags: Dict[str, str] = None):
        """カウンターメトリクスの記録"""
        self.record_metric(name, value, MetricType.COUNTER, tags)
    
    def record_gauge(self, name: str, value: float, tags: Dict[str, str] = None, unit: str = ""):
        """ゲージメトリクスの記録"""
        self.record_metric(name, value, MetricType.GAUGE, tags, unit)
    
    def record_timer(self, name: str, duration_ms: float, tags: Dict[str, str] = None):
        """タイマーメトリクスの記録"""
        self.record_metric(name, duration_ms, MetricType.TIMER, tags, "ms")
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """ヒストグラムメトリクスの記録"""
        self.record_metric(name, value, MetricType.HISTOGRAM, tags)
    
    def track_performance(self, operation: str, duration_ms: float, 
                         success: bool = True, metadata: Dict[str, Any] = None):
        """パフォーマンス追跡"""
        try:
            perf_data = {
                'operation': operation,
                'duration_ms': duration_ms,
                'success': success,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'metadata': metadata or {}
            }
            
            with self.performance_lock:
                self.performance_data[operation].append(perf_data)
                
                # 古いデータの削除（最新1000件のみ保持）
                if len(self.performance_data[operation]) > 1000:
                    self.performance_data[operation] = self.performance_data[operation][-1000:]
            
            # メトリクスとして記録
            tags = {'operation': operation, 'success': str(success)}
            self.record_timer(f"performance.{operation}", duration_ms, tags)
            
            # エラー率の計算とアラート
            if not success:
                self._check_error_rate(operation)
            
        except Exception as e:
            self.logger.error(f"Failed to track performance for {operation}: {e}")
    
    def create_alert(self, severity: AlertSeverity, title: str, message: str,
                    source: str = "system", metadata: Dict[str, Any] = None) -> str:
        """アラートの作成"""
        try:
            alert_id = f"{source}_{int(time.time() * 1000)}"
            
            alert = Alert(
                id=alert_id,
                severity=severity,
                title=title,
                message=message,
                source=source,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {}
            )
            
            with self.alert_lock:
                self.alerts[alert_id] = alert
                self.stats['total_alerts'] += 1
                self.stats['active_alerts'] += 1
            
            # アラートハンドラーの実行
            self._trigger_alert_handlers(alert)
            
            self.logger.warning(f"Alert created: {title} ({severity.value})")
            return alert_id
            
        except Exception as e:
            self.logger.error(f"Failed to create alert: {e}")
            return ""
    
    def resolve_alert(self, alert_id: str, resolution_note: str = ""):
        """アラートの解決"""
        try:
            with self.alert_lock:
                if alert_id in self.alerts:
                    alert = self.alerts[alert_id]
                    alert.resolved = True
                    alert.resolved_at = datetime.now(timezone.utc)
                    alert.metadata['resolution_note'] = resolution_note
                    
                    self.stats['active_alerts'] -= 1
                    
                    self.logger.info(f"Alert resolved: {alert.title}")
                else:
                    self.logger.warning(f"Alert not found: {alert_id}")
                    
        except Exception as e:
            self.logger.error(f"Failed to resolve alert {alert_id}: {e}")
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """アラートハンドラーの追加"""
        self.alert_handlers.append(handler)
    
    def get_metrics(self, name_pattern: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """メトリクスの取得"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            with self.metrics_lock:
                filtered_metrics = []
                
                for metric in self.metrics_buffer:
                    if metric.timestamp < cutoff_time:
                        continue
                    
                    if name_pattern and name_pattern not in metric.name:
                        continue
                    
                    filtered_metrics.append({
                        'name': metric.name,
                        'value': metric.value,
                        'type': metric.metric_type.value,
                        'tags': metric.tags,
                        'timestamp': metric.timestamp.isoformat(),
                        'unit': metric.unit
                    })
                
                return filtered_metrics
                
        except Exception as e:
            self.logger.error(f"Failed to get metrics: {e}")
            return []
    
    def get_alerts(self, severity: AlertSeverity = None, 
                  active_only: bool = False, hours: int = 24) -> List[Dict[str, Any]]:
        """アラートの取得"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            with self.alert_lock:
                filtered_alerts = []
                
                for alert in self.alerts.values():
                    if alert.timestamp < cutoff_time:
                        continue
                    
                    if severity and alert.severity != severity:
                        continue
                    
                    if active_only and alert.resolved:
                        continue
                    
                    filtered_alerts.append({
                        'id': alert.id,
                        'severity': alert.severity.value,
                        'title': alert.title,
                        'message': alert.message,
                        'source': alert.source,
                        'timestamp': alert.timestamp.isoformat(),
                        'resolved': alert.resolved,
                        'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                        'metadata': alert.metadata
                    })
                
                # 新しい順にソート
                filtered_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
                return filtered_alerts
                
        except Exception as e:
            self.logger.error(f"Failed to get alerts: {e}")
            return []
    
    def get_performance_stats(self, operation: str = None, hours: int = 24) -> Dict[str, Any]:
        """パフォーマンス統計の取得"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            with self.performance_lock:
                if operation:
                    operations = {operation: self.performance_data.get(operation, [])}
                else:
                    operations = dict(self.performance_data)
                
                stats = {}
                
                for op_name, op_data in operations.items():
                    # 時間範囲でフィルタ
                    recent_data = [
                        d for d in op_data 
                        if datetime.fromisoformat(d['timestamp'].replace('Z', '+00:00')) > cutoff_time
                    ]
                    
                    if not recent_data:
                        continue
                    
                    # 統計計算
                    durations = [d['duration_ms'] for d in recent_data]
                    successes = [d for d in recent_data if d['success']]
                    
                    stats[op_name] = {
                        'total_requests': len(recent_data),
                        'successful_requests': len(successes),
                        'error_rate': (len(recent_data) - len(successes)) / len(recent_data) * 100,
                        'avg_duration_ms': sum(durations) / len(durations),
                        'min_duration_ms': min(durations),
                        'max_duration_ms': max(durations),
                        'p95_duration_ms': self._calculate_percentile(durations, 95),
                        'p99_duration_ms': self._calculate_percentile(durations, 99)
                    }
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get performance stats: {e}")
            return {}
    
    def get_system_overview(self) -> Dict[str, Any]:
        """システム概要の取得"""
        try:
            uptime_seconds = time.time() - self.stats['start_time']
            
            # 最新メトリクスの取得
            recent_metrics = self.get_metrics(hours=1)
            
            # アクティブアラートの取得
            active_alerts = self.get_alerts(active_only=True, hours=24)
            
            # パフォーマンス統計
            perf_stats = self.get_performance_stats(hours=1)
            
            return {
                'uptime_seconds': uptime_seconds,
                'uptime_human': self._format_duration(uptime_seconds),
                'total_metrics': self.stats['total_metrics'],
                'total_alerts': self.stats['total_alerts'],
                'active_alerts': self.stats['active_alerts'],
                'recent_metrics_count': len(recent_metrics),
                'performance_operations': len(perf_stats),
                'alert_summary': self._get_alert_summary(active_alerts),
                'system_health': self._assess_system_health(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system overview: {e}")
            return {'error': str(e)}
    
    def start_background_tasks(self):
        """バックグラウンドタスクの開始"""
        if not self.running:
            self.running = True
            self.background_thread = threading.Thread(target=self._background_worker, daemon=True)
            self.background_thread.start()
            self.logger.info("Background monitoring tasks started")
    
    def stop_background_tasks(self):
        """バックグラウンドタスクの停止"""
        self.running = False
        if self.background_thread:
            self.background_thread.join(timeout=5)
        self.logger.info("Background monitoring tasks stopped")
    
    def _background_worker(self):
        """バックグラウンドワーカー"""
        while self.running:
            try:
                # メトリクスのクリーンアップ（古いデータの削除）
                self._cleanup_old_data()
                
                # システムメトリクスの収集
                self._collect_system_metrics()
                
                # アラートの自動解決チェック
                self._check_auto_resolve_alerts()
                
                # 30秒待機
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Background worker error: {e}")
                time.sleep(60)  # エラー時は長めに待機
    
    def _save_metric_to_db(self, metric: Metric):
        """メトリクスをデータベースに保存"""
        try:
            if not self.db:
                return
            
            # 非同期でデータベースに保存
            threading.Thread(
                target=self._save_metric_async,
                args=(metric,),
                daemon=True
            ).start()
            
        except Exception as e:
            self.logger.error(f"Failed to save metric to database: {e}")
    
    def _save_metric_async(self, metric: Metric):
        """メトリクスの非同期保存"""
        try:
            sql = """
            INSERT INTO system_metrics 
            (metric_name, metric_value, metric_type, tags, recorded_at)
            VALUES (?, ?, ?, ?, ?)
            """
            
            # DatabaseManagerの実際のメソッドを使用
            if hasattr(self.db, 'execute_with_retry'):
                self.db.execute_with_retry(sql, (
                    metric.name,
                    metric.value,
                    metric.metric_type.value,
                    json.dumps(metric.tags),
                    metric.timestamp
                ))
            elif hasattr(self.db, 'execute'):
                self.db.execute(sql, (
                    metric.name,
                    metric.value,
                    metric.metric_type.value,
                    json.dumps(metric.tags),
                    metric.timestamp
                ))
            
        except Exception as e:
            self.logger.error(f"Failed to save metric async: {e}")
    
    def _check_thresholds(self, metric: Metric):
        """閾値チェック"""
        try:
            threshold_key = metric.name.replace('.', '_')
            
            if threshold_key in self.thresholds:
                threshold = self.thresholds[threshold_key]
                
                if metric.value > threshold:
                    severity = AlertSeverity.HIGH if metric.value > threshold * 1.2 else AlertSeverity.MEDIUM
                    
                    self.create_alert(
                        severity=severity,
                        title=f"Threshold Exceeded: {metric.name}",
                        message=f"{metric.name} is {metric.value}{metric.unit}, exceeding threshold of {threshold}{metric.unit}",
                        source="threshold_monitor",
                        metadata={
                            'metric_name': metric.name,
                            'current_value': metric.value,
                            'threshold': threshold,
                            'unit': metric.unit
                        }
                    )
                    
        except Exception as e:
            self.logger.error(f"Threshold check failed: {e}")
    
    def _check_error_rate(self, operation: str):
        """エラー率チェック"""
        try:
            with self.performance_lock:
                recent_data = self.performance_data[operation][-100:]  # 最新100件
                
                if len(recent_data) >= 10:  # 最低10件のデータが必要
                    error_count = sum(1 for d in recent_data if not d['success'])
                    error_rate = (error_count / len(recent_data)) * 100
                    
                    if error_rate > self.thresholds['error_rate_percent']:
                        self.create_alert(
                            severity=AlertSeverity.HIGH,
                            title=f"High Error Rate: {operation}",
                            message=f"Error rate for {operation} is {error_rate:.1f}%, exceeding threshold of {self.thresholds['error_rate_percent']}%",
                            source="error_rate_monitor",
                            metadata={
                                'operation': operation,
                                'error_rate': error_rate,
                                'error_count': error_count,
                                'total_requests': len(recent_data)
                            }
                        )
                        
        except Exception as e:
            self.logger.error(f"Error rate check failed: {e}")
    
    def _trigger_alert_handlers(self, alert: Alert):
        """アラートハンドラーの実行"""
        for handler in self.alert_handlers:
            try:
                threading.Thread(target=handler, args=(alert,), daemon=True).start()
            except Exception as e:
                self.logger.error(f"Alert handler failed: {e}")
    
    def _default_alert_handler(self, alert: Alert):
        """デフォルトアラートハンドラー"""
        try:
            # ログに記録
            log_level = {
                AlertSeverity.LOW: logging.INFO,
                AlertSeverity.MEDIUM: logging.WARNING,
                AlertSeverity.HIGH: logging.ERROR,
                AlertSeverity.CRITICAL: logging.CRITICAL
            }.get(alert.severity, logging.WARNING)
            
            self.logger.log(log_level, f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message}")
            
            # 重要なアラートの場合は追加処理
            if alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
                # 本番環境では外部通知システムと連携
                self._send_external_notification(alert)
                
        except Exception as e:
            self.logger.error(f"Default alert handler failed: {e}")
    
    def _send_external_notification(self, alert: Alert):
        """外部通知の送信"""
        try:
            # 本番環境では Slack、メール、PagerDuty等と連携
            notification_data = {
                'alert_id': alert.id,
                'severity': alert.severity.value,
                'title': alert.title,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat()
            }
            
            # 開発環境では単純にログ出力
            self.logger.critical(f"EXTERNAL NOTIFICATION: {json.dumps(notification_data)}")
            
        except Exception as e:
            self.logger.error(f"External notification failed: {e}")
    
    def _cleanup_old_data(self):
        """古いデータのクリーンアップ"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            
            # 古いアラートの削除
            with self.alert_lock:
                old_alerts = [
                    alert_id for alert_id, alert in self.alerts.items()
                    if alert.timestamp < cutoff_time and alert.resolved
                ]
                
                for alert_id in old_alerts:
                    del self.alerts[alert_id]
            
            # データベースの古いメトリクスを削除
            if self.db:
                cleanup_sql = """
                DELETE FROM system_metrics 
                WHERE recorded_at < ?
                """
                if hasattr(self.db, 'execute_with_retry'):
                    self.db.execute_with_retry(cleanup_sql, (cutoff_time,))
                elif hasattr(self.db, 'execute'):
                    self.db.execute(cleanup_sql, (cutoff_time,))
                
        except Exception as e:
            self.logger.error(f"Data cleanup failed: {e}")
    
    def _collect_system_metrics(self):
        """システムメトリクスの収集"""
        try:
            import psutil
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_gauge("system.cpu_percent", cpu_percent, unit="%")
            
            # メモリ使用率
            memory = psutil.virtual_memory()
            self.record_gauge("system.memory_percent", memory.percent, unit="%")
            self.record_gauge("system.memory_available_gb", memory.available / (1024**3), unit="GB")
            
            # ディスク使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.record_gauge("system.disk_percent", disk_percent, unit="%")
            self.record_gauge("system.disk_free_gb", disk.free / (1024**3), unit="GB")
            
            # ネットワーク統計
            net_io = psutil.net_io_counters()
            self.record_counter("system.network_bytes_sent", net_io.bytes_sent)
            self.record_counter("system.network_bytes_recv", net_io.bytes_recv)
            
        except Exception as e:
            self.logger.error(f"System metrics collection failed: {e}")
    
    def _check_auto_resolve_alerts(self):
        """アラートの自動解決チェック"""
        try:
            # 1時間以上前のアラートで条件が改善されたものを自動解決
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
            
            with self.alert_lock:
                for alert in self.alerts.values():
                    if (not alert.resolved and 
                        alert.timestamp < cutoff_time and 
                        alert.source == "threshold_monitor"):
                        
                        # 閾値アラートの場合、現在の値をチェック
                        if self._should_auto_resolve_alert(alert):
                            self.resolve_alert(alert.id, "Auto-resolved: condition improved")
                            
        except Exception as e:
            self.logger.error(f"Auto-resolve check failed: {e}")
    
    def _should_auto_resolve_alert(self, alert: Alert) -> bool:
        """アラートを自動解決すべきかチェック"""
        try:
            # 簡単な実装: 閾値アラートの場合、最新のメトリクスをチェック
            metric_name = alert.metadata.get('metric_name')
            threshold = alert.metadata.get('threshold')
            
            if metric_name and threshold:
                recent_metrics = self.get_metrics(metric_name, hours=1)
                if recent_metrics:
                    latest_value = recent_metrics[-1]['value']
                    return latest_value <= threshold
            
            return False
            
        except Exception as e:
            self.logger.error(f"Auto-resolve check failed for alert {alert.id}: {e}")
            return False
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """パーセンタイル計算"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _format_duration(self, seconds: float) -> str:
        """期間のフォーマット"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        elif seconds < 86400:
            return f"{seconds/3600:.1f}h"
        else:
            return f"{seconds/86400:.1f}d"
    
    def _get_alert_summary(self, alerts: List[Dict[str, Any]]) -> Dict[str, int]:
        """アラートサマリーの取得"""
        summary = {severity.value: 0 for severity in AlertSeverity}
        
        for alert in alerts:
            severity = alert['severity']
            if severity in summary:
                summary[severity] += 1
        
        return summary
    
    def _assess_system_health(self) -> str:
        """システム健全性の評価"""
        try:
            active_alerts = self.stats['active_alerts']
            
            if active_alerts == 0:
                return "healthy"
            elif active_alerts <= 2:
                return "warning"
            else:
                return "critical"
                
        except Exception:
            return "unknown"