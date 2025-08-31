"""
ProductionConfig - 本番環境設定クラス
セキュリティを重視した本番環境用の設定
"""
import os
import secrets
from typing import Optional


class BaseConfig:
    """基本設定クラス"""
    
    # セキュリティ設定
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1時間
    
    # データベース設定
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///tou_connect.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Redis設定（キャッシュ・セッション用）
    REDIS_URL = os.environ.get('REDIS_URL')
    
    # 外部API設定
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    TWITTER_BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')
    
    # アプリケーション設定
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    JSON_SORT_KEYS = False
    
    # セッション設定
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1時間
    
    # ログ設定
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'


class DevelopmentConfig(BaseConfig):
    """開発環境設定"""
    
    DEBUG = True
    TESTING = False
    
    # 開発環境では緩いセキュリティ設定
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False
    
    # 開発用データベース
    DATABASE_URL = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///tou_connect_dev.db'
    
    # 開発用ログレベル
    LOG_LEVEL = 'DEBUG'


class TestingConfig(BaseConfig):
    """テスト環境設定"""
    
    DEBUG = False
    TESTING = True
    
    # テスト用データベース（メモリ）
    DATABASE_URL = 'sqlite:///:memory:'
    
    # テスト用Redis（オプション）
    REDIS_URL = None
    
    # テスト用セキュリティ設定
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    SESSION_COOKIE_SECURE = False
    
    # テスト用ログレベル
    LOG_LEVEL = 'WARNING'


class ProductionConfig(BaseConfig):
    """本番環境設定"""
    
    DEBUG = False
    TESTING = False
    
    # 本番環境必須設定の検証
    def __init__(self):
        self._validate_production_settings()
    
    def _validate_production_settings(self):
        """本番環境設定の検証"""
        required_vars = [
            'SECRET_KEY',
            'DATABASE_URL',
            'GEMINI_API_KEY',
            'TWITTER_BEARER_TOKEN'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"本番環境で必要な環境変数が設定されていません: {', '.join(missing_vars)}")
        
        # SECRET_KEYの強度チェック
        secret_key = os.environ.get('SECRET_KEY')
        if secret_key == 'dev-secret-key' or len(secret_key) < 32:
            raise ValueError("本番環境では強力なSECRET_KEYが必要です")
    
    # 本番環境固有設定
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # データベース設定（PostgreSQL推奨）
    DATABASE_URL = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # Redis設定（本番環境では必須）
    REDIS_URL = os.environ.get('REDIS_URL')
    if not REDIS_URL and os.environ.get('ENVIRONMENT') == 'production':
        raise ValueError("本番環境ではREDIS_URLが必要です")
    
    # セキュリティ強化設定
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    WTF_CSRF_ENABLED = True
    
    # HTTPS強制
    PREFERRED_URL_SCHEME = 'https'
    
    # ログ設定
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING')
    
    # パフォーマンス設定
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1年間のキャッシュ
    
    # 監視・メトリクス設定
    ENABLE_METRICS = True
    METRICS_ENDPOINT = '/metrics'
    
    # レート制限設定
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = "1000 per hour"
    
    # 外部サービス設定
    SECRETS_PROVIDER = os.environ.get('SECRETS_PROVIDER', 'aws')  # aws, azure, env
    AWS_REGION = os.environ.get('AWS_REGION', 'ap-northeast-1')
    AZURE_KEY_VAULT_URL = os.environ.get('AZURE_KEY_VAULT_URL')


class StagingConfig(ProductionConfig):
    """ステージング環境設定"""
    
    DEBUG = False
    TESTING = False
    
    # ステージング用データベース
    DATABASE_URL = os.environ.get('STAGING_DATABASE_URL')
    
    # ステージング用ログレベル
    LOG_LEVEL = 'INFO'
    
    # ステージング用セキュリティ設定（本番より緩い）
    SESSION_COOKIE_SAMESITE = 'Lax'


def get_config(environment: Optional[str] = None) -> BaseConfig:
    """環境に応じた設定クラスを取得"""
    if environment is None:
        environment = os.environ.get('ENVIRONMENT', 'development')
    
    config_mapping = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'staging': StagingConfig,
        'production': ProductionConfig
    }
    
    config_class = config_mapping.get(environment.lower())
    if not config_class:
        raise ValueError(f"Unknown environment: {environment}")
    
    return config_class()


def validate_environment():
    """環境設定の検証"""
    environment = os.environ.get('ENVIRONMENT', 'development')
    
    try:
        config = get_config(environment)
        print(f"✅ {environment.title()} environment configuration validated successfully")
        return True
    except Exception as e:
        print(f"❌ {environment.title()} environment configuration validation failed: {e}")
        return False


if __name__ == '__main__':
    # 設定検証スクリプト
    import sys
    
    if len(sys.argv) > 1:
        env = sys.argv[1]
    else:
        env = os.environ.get('ENVIRONMENT', 'development')
    
    print(f"Validating {env} environment configuration...")
    
    if validate_environment():
        sys.exit(0)
    else:
        sys.exit(1)