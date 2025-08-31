"""
LoggingManager - 構造化ログシステム
本番環境での詳細なログ管理とモニタリング機能を提供
"""
import os
import json
import logging
import logging.handlers
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """構造化ログフォーマッター"""
    
    def format(self, record):
        """ログレコードをJSON形式でフォーマット"""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 追加のコンテキスト情報
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        
        if hasattr(record, 'user_agent'):
            log_entry['user_agent'] = record.user_agent
        
        if hasattr(record, 'execution_time'):
            log_entry['execution_time_ms'] = record.execution_time
        
        # エラー情報
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # 環境情報
        log_entry['environment'] = os.getenv('ENVIRONMENT', 'development')
        log_entry['service'] = 'tou_connect'
        
        return json.dumps(log_entry, ensure_ascii=False)


class LoggingManager:
    """構造化ログ管理クラス"""
    
    def __init__(self, app_name: str = 'tou_connect'):
        self.app_name = app_name
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # ログディレクトリの作成
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        
        # ロガーの設定
        self.setup_logging()
    
    def setup_logging(self):
        """ログ設定の初期化"""
        # ルートロガーの設定
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level))
        
        # 既存のハンドラーをクリア
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 環境に応じたハンドラー設定
        if self.environment == 'production':
            self._setup_production_logging()
        elif self.environment == 'development':
            self._setup_development_logging()
        else:
            self._setup_testing_logging()
    
    def _setup_production_logging(self):
        """本番環境ログ設定"""
        root_logger = logging.getLogger()
        
        # アプリケーションログ（構造化JSON）
        app_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'app.json',
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10
        )
        app_handler.setFormatter(StructuredFormatter())
        app_handler.setLevel(logging.INFO)
        root_logger.addHandler(app_handler)
        
        # エラーログ（重要なエラーのみ）
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'error.json',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setFormatter(StructuredFormatter())
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
        
        # セキュリティログ
        security_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'security.json',
            maxBytes=20*1024*1024,  # 20MB
            backupCount=10
        )
        security_handler.setFormatter(StructuredFormatter())
        security_handler.addFilter(SecurityLogFilter())
        root_logger.addHandler(security_handler)
        
        # コンソール出力（最小限）
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(StructuredFormatter())
        console_handler.setLevel(logging.WARNING)
        root_logger.addHandler(console_handler)
    
    def _setup_development_logging(self):
        """開発環境ログ設定"""
        root_logger = logging.getLogger()
        
        # コンソール出力（人間が読みやすい形式）
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
        
        # ファイル出力（構造化JSON）
        file_handler = logging.FileHandler(self.log_dir / 'development.json')
        file_handler.setFormatter(StructuredFormatter())
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
    
    def _setup_testing_logging(self):
        """テスト環境ログ設定"""
        root_logger = logging.getLogger()
        
        # テスト時は最小限のログ
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.WARNING)
        root_logger.addHandler(console_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """名前付きロガーの取得"""
        return logging.getLogger(name)
    
    def log_user_action(self, logger: logging.Logger, user_id: int, action: str, 
                       details: Dict[str, Any] = None, request_context: Dict[str, Any] = None):
        """ユーザーアクションのログ記録"""
        extra = {
            'user_id': user_id,
            'action': action
        }
        
        if request_context:
            extra.update({
                'request_id': request_context.get('request_id'),
                'ip_address': request_context.get('ip_address'),
                'user_agent': request_context.get('user_agent')
            })
        
        message = f"User action: {action}"
        if details:
            message += f" - {json.dumps(details, ensure_ascii=False)}"
        
        logger.info(message, extra=extra)
    
    def log_security_event(self, logger: logging.Logger, event_type: str, 
                          severity: str, details: Dict[str, Any] = None,
                          request_context: Dict[str, Any] = None):
        """セキュリティイベントのログ記録"""
        extra = {
            'security_event': True,
            'event_type': event_type,
            'severity': severity
        }
        
        if request_context:
            extra.update({
                'request_id': request_context.get('request_id'),
                'ip_address': request_context.get('ip_address'),
                'user_agent': request_context.get('user_agent')
            })
        
        message = f"Security event: {event_type} (severity: {severity})"
        if details:
            message += f" - {json.dumps(details, ensure_ascii=False)}"
        
        if severity in ['high', 'critical']:
            logger.error(message, extra=extra)
        else:
            logger.warning(message, extra=extra)
    
    def log_performance_metric(self, logger: logging.Logger, metric_name: str, 
                             value: float, unit: str = 'ms',
                             request_context: Dict[str, Any] = None):
        """パフォーマンスメトリクスのログ記録"""
        extra = {
            'performance_metric': True,
            'metric_name': metric_name,
            'metric_value': value,
            'unit': unit
        }
        
        if request_context:
            extra.update({
                'request_id': request_context.get('request_id'),
                'execution_time': value
            })
        
        message = f"Performance metric: {metric_name} = {value}{unit}"
        logger.info(message, extra=extra)
    
    def log_api_request(self, logger: logging.Logger, method: str, path: str,
                       status_code: int, response_time_ms: float,
                       request_context: Dict[str, Any] = None):
        """APIリクエストのログ記録"""
        extra = {
            'api_request': True,
            'method': method,
            'path': path,
            'status_code': status_code,
            'response_time_ms': response_time_ms
        }
        
        if request_context:
            extra.update(request_context)
        
        message = f"{method} {path} - {status_code} ({response_time_ms}ms)"
        
        if status_code >= 500:
            logger.error(message, extra=extra)
        elif status_code >= 400:
            logger.warning(message, extra=extra)
        else:
            logger.info(message, extra=extra)
    
    def cleanup_old_logs(self, days: int = 30):
        """古いログファイルのクリーンアップ"""
        try:
            import time
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            
            for log_file in self.log_dir.glob('*.json*'):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    logging.info(f"Deleted old log file: {log_file}")
                    
        except Exception as e:
            logging.error(f"Log cleanup failed: {e}")


class SecurityLogFilter(logging.Filter):
    """セキュリティログフィルター"""
    
    def filter(self, record):
        """セキュリティ関連のログのみを通す"""
        return hasattr(record, 'security_event') and record.security_event


class RequestContextManager:
    """リクエストコンテキスト管理"""
    
    def __init__(self):
        self.context = {}
    
    def set_request_context(self, request_id: str, ip_address: str = None, 
                           user_agent: str = None, user_id: int = None):
        """リクエストコンテキストの設定"""
        self.context = {
            'request_id': request_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'user_id': user_id
        }
    
    def get_context(self) -> Dict[str, Any]:
        """現在のコンテキストを取得"""
        return self.context.copy()
    
    def clear_context(self):
        """コンテキストをクリア"""
        self.context = {}


# グローバルインスタンス
logging_manager = LoggingManager()
request_context = RequestContextManager()


def get_logger(name: str) -> logging.Logger:
    """ロガー取得のヘルパー関数"""
    return logging_manager.get_logger(name)


def log_user_action(user_id: int, action: str, details: Dict[str, Any] = None):
    """ユーザーアクションログのヘルパー関数"""
    logger = get_logger('user_actions')
    logging_manager.log_user_action(
        logger, user_id, action, details, 
        request_context.get_context()
    )


def log_security_event(event_type: str, severity: str, details: Dict[str, Any] = None):
    """セキュリティイベントログのヘルパー関数"""
    logger = get_logger('security')
    logging_manager.log_security_event(
        logger, event_type, severity, details,
        request_context.get_context()
    )