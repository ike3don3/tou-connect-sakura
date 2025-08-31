"""
AlertManager - 高度なアラート管理システム
閾値ベースアラート、アラート集約、通知チャネル管理
"""
import os
import json
import time
import logging
import smtplib
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from monitoring.monitoring_manager import MonitoringManager, AlertSeverity, Alert


class NotificationChannel(Enum):
    """通知チャネル"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


class AlertRule(Enum):
    """アラートルール種別"""
    THRESHOLD = "threshold"
    RATE_OF_CHANGE = "rate_of_change"
    ANOMALY = "anomaly"
    COMPOSITE = "composite"


@dataclass
class ThresholdRule:
    """閾値ルール"""
    metric_name: str
    operator: str  # >, <, >=, <=, ==, !=
    threshold_value: float
    duration_minutes: int = 5
    severity: AlertSeverity = AlertSeverity.MEDIUM
    enabled: bool = True
    description: str = ""


@dataclass
class NotificationConfig:
    """通知設定"""
    channel: NotificationChannel
    enabled: bool = True
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


@dataclass
class AlertAggregation:
    """アラート集約設定"""
    group_by: List[str]  # グループ化するフィールド
    time_window_minutes: int = 15
    max_alerts_per_group: int = 5
    enabled: bool = True


class AlertManager:
    """高度なアラート管理システム"""
    
    def __init__(self, monitoring_manager: MonitoringManager, db_manager=None):
        self.monitoring = monitoring_manager
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        
        # アラートルール
        self.threshold_rules: Dict[str, ThresholdRule] = {}
        self.custom_rules: Dict[str, Callable] = {}
        
        # 通知設定
        self.notification_channels: Dict[str, NotificationConfig] = {}
        
        # アラート集約
        self.aggregation_config = AlertAggregation(
            group_by=['source', 'severity'],
            time_window_minutes=15,
            max_alerts_per_group=5
        )
        
        # アラート履歴
        self.alert_history: List[Dict[str, Any]] = []
        self.suppressed_alerts: Dict[str, datetime] = {}
        
        # 統計情報
        self.stats = {
            'total_rules': 0,
            'active_rules': 0,
            'notifications_sent': 0,
            'suppressed_alerts': 0
        }
        
        # 初期化
        self._init_alert_manager()
    
    def _init_alert_manager(self):
        """アラートマネージャーの初期化"""
        try:
            # デフォルトルールの設定
            self._setup_default_rules()
            
            # 通知チャネルの設定
            self._setup_notification_channels()
            
            # MonitoringManagerにアラートハンドラーを追加
            self.monitoring.add_alert_handler(self._handle_alert)
            
            self.logger.info("Alert manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Alert manager initialization failed: {e}")
            raise
    
    def _setup_default_rules(self):
        """デフォルトアラートルールの設定"""
        default_rules = [
            ThresholdRule(
                metric_name="system.cpu.usage_percent",
                operator=">=",
                threshold_value=80.0,
                duration_minutes=5,
                severity=AlertSeverity.HIGH,
                description="CPU使用率が高い"
            ),
            ThresholdRule(
                metric_name="system.memory.usage_percent",
                operator=">=",
                threshold_value=85.0,
                duration_minutes=5,
                severity=AlertSeverity.HIGH,
                description="メモリ使用率が高い"
            ),
            ThresholdRule(
                metric_name="system.disk.usage_percent",
                operator=">=",
                threshold_value=90.0,
                duration_minutes=10,
                severity=AlertSeverity.CRITICAL,
                description="ディスク使用率が危険レベル"
            ),
            ThresholdRule(
                metric_name="http.request.duration",
                operator=">=",
                threshold_value=3000.0,
                duration_minutes=3,
                severity=AlertSeverity.MEDIUM,
                description="HTTPレスポンス時間が遅い"
            ),
            ThresholdRule(
                metric_name="database.health_check.response_time",
                operator=">=",
                threshold_value=1000.0,
                duration_minutes=2,
                severity=AlertSeverity.HIGH,
                description="データベース応答時間が遅い"
            )
        ]
        
        for rule in default_rules:
            self.add_threshold_rule(rule)
    
    def _setup_notification_channels(self):
        """通知チャネルの設定"""
        # 環境変数から設定を読み込み
        
        # Email設定
        if os.getenv('SMTP_HOST'):
            email_config = NotificationConfig(
                channel=NotificationChannel.EMAIL,
                enabled=True,
                config={
                    'smtp_host': os.getenv('SMTP_HOST'),
                    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
                    'smtp_user': os.getenv('SMTP_USER'),
                    'smtp_password': os.getenv('SMTP_PASSWORD'),
                    'from_email': os.getenv('ALERT_FROM_EMAIL'),
                    'to_emails': os.getenv('ALERT_TO_EMAILS', '').split(',')
                }
            )
            self.notification_channels['email'] = email_config
        
        # Slack設定
        if os.getenv('SLACK_WEBHOOK_URL'):
            slack_config = NotificationConfig(
                channel=NotificationChannel.SLACK,
                enabled=True,
                config={
                    'webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
                    'channel': os.getenv('SLACK_CHANNEL', '#alerts'),
                    'username': os.getenv('SLACK_USERNAME', 'TOU Connect Monitor')
                }
            )
            self.notification_channels['slack'] = slack_config
        
        # Webhook設定
        if os.getenv('ALERT_WEBHOOK_URL'):
            webhook_config = NotificationConfig(
                channel=NotificationChannel.WEBHOOK,
                enabled=True,
                config={
                    'webhook_url': os.getenv('ALERT_WEBHOOK_URL'),
                    'headers': json.loads(os.getenv('ALERT_WEBHOOK_HEADERS', '{}'))
                }
            )
            self.notification_channels['webhook'] = webhook_config
    
    def add_threshold_rule(self, rule: ThresholdRule) -> str:
        """閾値ルールの追加"""
        rule_id = f"threshold_{rule.metric_name}_{rule.operator}_{rule.threshold_value}"
        self.threshold_rules[rule_id] = rule
        
        self.stats['total_rules'] += 1
        if rule.enabled:
            self.stats['active_rules'] += 1
        
        self.logger.info(f"Added threshold rule: {rule_id}")
        return rule_id
    
    def remove_threshold_rule(self, rule_id: str) -> bool:
        """閾値ルールの削除"""
        if rule_id in self.threshold_rules:
            rule = self.threshold_rules[rule_id]
            del self.threshold_rules[rule_id]
            
            self.stats['total_rules'] -= 1
            if rule.enabled:
                self.stats['active_rules'] -= 1
            
            self.logger.info(f"Removed threshold rule: {rule_id}")
            return True
        return False
    
    def add_custom_rule(self, rule_name: str, rule_func: Callable) -> str:
        """カスタムルールの追加"""
        self.custom_rules[rule_name] = rule_func
        self.stats['total_rules'] += 1
        self.stats['active_rules'] += 1
        
        self.logger.info(f"Added custom rule: {rule_name}")
        return rule_name
    
    def evaluate_threshold_rules(self, metrics: List[Dict[str, Any]]):
        """閾値ルールの評価"""
        try:
            # メトリクス名でグループ化
            metrics_by_name = {}
            for metric in metrics:
                name = metric['name']
                if name not in metrics_by_name:
                    metrics_by_name[name] = []
                metrics_by_name[name].append(metric)
            
            # 各ルールを評価
            for rule_id, rule in self.threshold_rules.items():
                if not rule.enabled:
                    continue
                
                if rule.metric_name not in metrics_by_name:
                    continue
                
                # 最新のメトリクス値を取得
                latest_metrics = sorted(
                    metrics_by_name[rule.metric_name],
                    key=lambda x: x['timestamp'],
                    reverse=True
                )
                
                if not latest_metrics:
                    continue
                
                latest_value = latest_metrics[0]['value']
                
                # 閾値チェック
                if self._evaluate_threshold(latest_value, rule.operator, rule.threshold_value):
                    # 持続時間チェック
                    if self._check_duration(rule, metrics_by_name[rule.metric_name]):
                        self._trigger_threshold_alert(rule, latest_value, latest_metrics[0])
                        
        except Exception as e:
            self.logger.error(f"Threshold rule evaluation failed: {e}")
    
    def _evaluate_threshold(self, value: float, operator: str, threshold: float) -> bool:
        """閾値評価"""
        operators = {
            '>': lambda x, y: x > y,
            '<': lambda x, y: x < y,
            '>=': lambda x, y: x >= y,
            '<=': lambda x, y: x <= y,
            '==': lambda x, y: x == y,
            '!=': lambda x, y: x != y
        }
        
        return operators.get(operator, lambda x, y: False)(value, threshold)
    
    def _check_duration(self, rule: ThresholdRule, metrics: List[Dict[str, Any]]) -> bool:
        """持続時間チェック"""
        if rule.duration_minutes <= 0:
            return True
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=rule.duration_minutes)
        
        # 指定期間内のメトリクスをチェック
        recent_metrics = [
            m for m in metrics
            if datetime.fromisoformat(m['timestamp'].replace('Z', '+00:00')) > cutoff_time
        ]
        
        if len(recent_metrics) < 2:  # 最低2つのデータポイントが必要
            return False
        
        # 全てのデータポイントが閾値を超えているかチェック
        violation_count = 0
        for metric in recent_metrics:
            if self._evaluate_threshold(metric['value'], rule.operator, rule.threshold_value):
                violation_count += 1
        
        # 80%以上のデータポイントが閾値を超えている場合にアラート
        return (violation_count / len(recent_metrics)) >= 0.8
    
    def _trigger_threshold_alert(self, rule: ThresholdRule, current_value: float, metric: Dict[str, Any]):
        """閾値アラートのトリガー"""
        alert_key = f"threshold_{rule.metric_name}_{rule.operator}_{rule.threshold_value}"
        
        # アラート抑制チェック
        if self._is_alert_suppressed(alert_key):
            return
        
        # アラート作成
        alert_id = self.monitoring.create_alert(
            severity=rule.severity,
            title=f"Threshold Alert: {rule.metric_name}",
            message=f"{rule.description or rule.metric_name} - Current: {current_value}, Threshold: {rule.threshold_value}",
            source="threshold_monitor",
            metadata={
                'rule_id': alert_key,
                'metric_name': rule.metric_name,
                'current_value': current_value,
                'threshold_value': rule.threshold_value,
                'operator': rule.operator,
                'metric_tags': metric.get('tags', {})
            }
        )
        
        # アラート抑制設定（同じアラートを15分間抑制）
        self.suppressed_alerts[alert_key] = datetime.now(timezone.utc) + timedelta(minutes=15)
        self.stats['suppressed_alerts'] += 1
    
    def _is_alert_suppressed(self, alert_key: str) -> bool:
        """アラート抑制チェック"""
        if alert_key not in self.suppressed_alerts:
            return False
        
        suppression_end = self.suppressed_alerts[alert_key]
        if datetime.now(timezone.utc) > suppression_end:
            del self.suppressed_alerts[alert_key]
            return False
        
        return True
    
    def _handle_alert(self, alert: Alert):
        """アラートハンドラー"""
        try:
            # アラート履歴に追加
            alert_data = {
                'id': alert.id,
                'severity': alert.severity.value,
                'title': alert.title,
                'message': alert.message,
                'source': alert.source,
                'timestamp': alert.timestamp.isoformat(),
                'metadata': alert.metadata
            }
            self.alert_history.append(alert_data)
            
            # 履歴サイズ制限（最新1000件のみ保持）
            if len(self.alert_history) > 1000:
                self.alert_history = self.alert_history[-1000:]
            
            # アラート集約チェック
            if self._should_aggregate_alert(alert):
                return
            
            # 通知送信
            self._send_notifications(alert)
            
        except Exception as e:
            self.logger.error(f"Alert handling failed: {e}")
    
    def _should_aggregate_alert(self, alert: Alert) -> bool:
        """アラート集約判定"""
        if not self.aggregation_config.enabled:
            return False
        
        # 時間窓内の同じグループのアラート数をチェック
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=self.aggregation_config.time_window_minutes)
        
        group_key = self._get_alert_group_key(alert)
        recent_alerts = [
            a for a in self.alert_history
            if (datetime.fromisoformat(a['timestamp']) > cutoff_time and
                self._get_alert_group_key_from_data(a) == group_key)
        ]
        
        return len(recent_alerts) >= self.aggregation_config.max_alerts_per_group
    
    def _get_alert_group_key(self, alert: Alert) -> str:
        """アラートグループキーの生成"""
        group_values = []
        for field in self.aggregation_config.group_by:
            if field == 'source':
                group_values.append(alert.source)
            elif field == 'severity':
                group_values.append(alert.severity.value)
            elif field in alert.metadata:
                group_values.append(str(alert.metadata[field]))
            else:
                group_values.append('unknown')
        
        return '|'.join(group_values)
    
    def _get_alert_group_key_from_data(self, alert_data: Dict[str, Any]) -> str:
        """アラートデータからグループキーを生成"""
        group_values = []
        for field in self.aggregation_config.group_by:
            if field == 'source':
                group_values.append(alert_data['source'])
            elif field == 'severity':
                group_values.append(alert_data['severity'])
            elif field in alert_data['metadata']:
                group_values.append(str(alert_data['metadata'][field]))
            else:
                group_values.append('unknown')
        
        return '|'.join(group_values)
    
    def _send_notifications(self, alert: Alert):
        """通知送信"""
        for channel_name, config in self.notification_channels.items():
            if not config.enabled:
                continue
            
            try:
                if config.channel == NotificationChannel.EMAIL:
                    self._send_email_notification(alert, config)
                elif config.channel == NotificationChannel.SLACK:
                    self._send_slack_notification(alert, config)
                elif config.channel == NotificationChannel.WEBHOOK:
                    self._send_webhook_notification(alert, config)
                
                self.stats['notifications_sent'] += 1
                
            except Exception as e:
                self.logger.error(f"Notification failed for {channel_name}: {e}")
    
    def _send_email_notification(self, alert: Alert, config: NotificationConfig):
        """Email通知送信"""
        smtp_config = config.config
        
        msg = MIMEMultipart()
        msg['From'] = smtp_config['from_email']
        msg['To'] = ', '.join(smtp_config['to_emails'])
        msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
        
        body = f"""
        アラートが発生しました。
        
        重要度: {alert.severity.value.upper()}
        タイトル: {alert.title}
        メッセージ: {alert.message}
        ソース: {alert.source}
        発生時刻: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        
        詳細情報:
        {json.dumps(alert.metadata, indent=2, ensure_ascii=False)}
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        with smtplib.SMTP(smtp_config['smtp_host'], smtp_config['smtp_port']) as server:
            server.starttls()
            server.login(smtp_config['smtp_user'], smtp_config['smtp_password'])
            server.send_message(msg)
    
    def _send_slack_notification(self, alert: Alert, config: NotificationConfig):
        """Slack通知送信"""
        slack_config = config.config
        
        color_map = {
            AlertSeverity.LOW: 'good',
            AlertSeverity.MEDIUM: 'warning',
            AlertSeverity.HIGH: 'danger',
            AlertSeverity.CRITICAL: 'danger'
        }
        
        payload = {
            'channel': slack_config['channel'],
            'username': slack_config['username'],
            'attachments': [{
                'color': color_map.get(alert.severity, 'warning'),
                'title': f"[{alert.severity.value.upper()}] {alert.title}",
                'text': alert.message,
                'fields': [
                    {'title': 'ソース', 'value': alert.source, 'short': True},
                    {'title': '発生時刻', 'value': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'short': True}
                ],
                'footer': 'TOU Connect Monitor',
                'ts': int(alert.timestamp.timestamp())
            }]
        }
        
        response = requests.post(slack_config['webhook_url'], json=payload, timeout=10)
        response.raise_for_status()
    
    def _send_webhook_notification(self, alert: Alert, config: NotificationConfig):
        """Webhook通知送信"""
        webhook_config = config.config
        
        payload = {
            'alert_id': alert.id,
            'severity': alert.severity.value,
            'title': alert.title,
            'message': alert.message,
            'source': alert.source,
            'timestamp': alert.timestamp.isoformat(),
            'metadata': alert.metadata
        }
        
        headers = webhook_config.get('headers', {})
        headers['Content-Type'] = 'application/json'
        
        response = requests.post(
            webhook_config['webhook_url'],
            json=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
    
    def get_alert_rules(self) -> Dict[str, Any]:
        """アラートルール一覧の取得"""
        return {
            'threshold_rules': {
                rule_id: asdict(rule) for rule_id, rule in self.threshold_rules.items()
            },
            'custom_rules': list(self.custom_rules.keys()),
            'stats': self.stats
        }
    
    def get_notification_channels(self) -> Dict[str, Any]:
        """通知チャネル一覧の取得"""
        channels = {}
        for name, config in self.notification_channels.items():
            channels[name] = {
                'channel': config.channel.value,
                'enabled': config.enabled,
                'config_keys': list(config.config.keys()) if config.config else []
            }
        return channels
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """アラート統計の取得"""
        now = datetime.now(timezone.utc)
        
        # 時間別統計
        hourly_stats = {}
        daily_stats = {}
        
        for alert in self.alert_history:
            alert_time = datetime.fromisoformat(alert['timestamp'])
            hour_key = alert_time.strftime('%Y-%m-%d %H:00')
            day_key = alert_time.strftime('%Y-%m-%d')
            
            if hour_key not in hourly_stats:
                hourly_stats[hour_key] = {'total': 0, 'by_severity': {}}
            if day_key not in daily_stats:
                daily_stats[day_key] = {'total': 0, 'by_severity': {}}
            
            severity = alert['severity']
            
            hourly_stats[hour_key]['total'] += 1
            hourly_stats[hour_key]['by_severity'][severity] = hourly_stats[hour_key]['by_severity'].get(severity, 0) + 1
            
            daily_stats[day_key]['total'] += 1
            daily_stats[day_key]['by_severity'][severity] = daily_stats[day_key]['by_severity'].get(severity, 0) + 1
        
        return {
            'total_alerts': len(self.alert_history),
            'suppressed_alerts': len(self.suppressed_alerts),
            'notifications_sent': self.stats['notifications_sent'],
            'hourly_stats': hourly_stats,
            'daily_stats': daily_stats,
            'rules_stats': {
                'total_rules': self.stats['total_rules'],
                'active_rules': self.stats['active_rules']
            }
        }
    
    def test_notification_channel(self, channel_name: str) -> bool:
        """通知チャネルのテスト"""
        if channel_name not in self.notification_channels:
            return False
        
        config = self.notification_channels[channel_name]
        
        # テストアラートを作成
        test_alert = Alert(
            id=f"test_{int(time.time())}",
            severity=AlertSeverity.LOW,
            title="Test Alert",
            message="This is a test alert from TOU Connect monitoring system.",
            source="alert_manager_test",
            timestamp=datetime.now(timezone.utc),
            metadata={'test': True}
        )
        
        try:
            if config.channel == NotificationChannel.EMAIL:
                self._send_email_notification(test_alert, config)
            elif config.channel == NotificationChannel.SLACK:
                self._send_slack_notification(test_alert, config)
            elif config.channel == NotificationChannel.WEBHOOK:
                self._send_webhook_notification(test_alert, config)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Test notification failed for {channel_name}: {e}")
            return False