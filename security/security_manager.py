"""
SecurityManager - セキュリティ基盤管理クラス
本番環境でのAPIキー管理、レート制限、セキュリティヘッダーを統合管理
"""
import os
import secrets
import logging
from typing import Dict, Optional, Any
from flask import Flask, request, Response, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

# 本番環境では boto3 や azure-keyvault-secrets を使用
try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


class SecurityManager:
    """セキュリティ管理の中央クラス"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.secrets_client = None
        self.rate_limiter = None
        self.logger = logging.getLogger(__name__)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Flaskアプリケーションの初期化"""
        self.app = app
        
        # 環境変数管理の初期化
        self._init_secrets_manager()
        
        # レート制限の初期化
        self._init_rate_limiter()
        
        # CORS設定
        self._init_cors()
        
        # セキュリティヘッダーの設定
        self._init_security_headers()
        
        self.logger.info("SecurityManager initialized successfully")
    
    def _init_secrets_manager(self):
        """環境変数管理サービスの初期化"""
        environment = os.getenv('ENVIRONMENT', 'development')
        
        if environment == 'production':
            # 本番環境: AWS Secrets Manager または Azure Key Vault
            secrets_provider = os.getenv('SECRETS_PROVIDER', 'aws')
            
            if secrets_provider == 'aws' and AWS_AVAILABLE:
                self._init_aws_secrets()
            elif secrets_provider == 'azure' and AZURE_AVAILABLE:
                self._init_azure_secrets()
            else:
                self.logger.warning("本番環境ですが、シークレット管理サービスが利用できません")
                self._init_env_fallback()
        else:
            # 開発環境: 環境変数フォールバック
            self._init_env_fallback()
    
    def _init_aws_secrets(self):
        """AWS Secrets Manager の初期化"""
        try:
            region = os.getenv('AWS_REGION', 'ap-northeast-1')
            self.secrets_client = boto3.client('secretsmanager', region_name=region)
            self.logger.info("AWS Secrets Manager initialized")
        except Exception as e:
            self.logger.error(f"AWS Secrets Manager initialization failed: {e}")
            self._init_env_fallback()
    
    def _init_azure_secrets(self):
        """Azure Key Vault の初期化"""
        try:
            vault_url = os.getenv('AZURE_KEY_VAULT_URL')
            if not vault_url:
                raise ValueError("AZURE_KEY_VAULT_URL not set")
            
            credential = DefaultAzureCredential()
            self.secrets_client = SecretClient(vault_url=vault_url, credential=credential)
            self.logger.info("Azure Key Vault initialized")
        except Exception as e:
            self.logger.error(f"Azure Key Vault initialization failed: {e}")
            self._init_env_fallback()
    
    def _init_env_fallback(self):
        """環境変数フォールバック"""
        self.secrets_client = None
        self.logger.info("Using environment variables for secrets")
    
    def _init_rate_limiter(self):
        """レート制限の初期化"""
        try:
            # Redis URLが設定されている場合はRedisを使用、そうでなければメモリ
            redis_url = self.get_secret('REDIS_URL')
            
            if redis_url:
                storage_uri = redis_url
            else:
                storage_uri = "memory://"
            
            self.rate_limiter = Limiter(
                app=self.app,
                key_func=get_remote_address,
                storage_uri=storage_uri,
                default_limits=["1000 per hour", "100 per minute"]
            )
            
            self.logger.info(f"Rate limiter initialized with storage: {storage_uri}")
        except Exception as e:
            self.logger.error(f"Rate limiter initialization failed: {e}")
    
    def _init_cors(self):
        """CORS設定の初期化"""
        environment = os.getenv('ENVIRONMENT', 'development')
        
        if environment == 'production':
            # 本番環境: 厳格なCORS設定
            allowed_origins_str = os.getenv('ALLOWED_ORIGINS', '')
            if allowed_origins_str:
                allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',') if origin.strip()]
                CORS(self.app, origins=allowed_origins)
                self.logger.info(f"CORS initialized with origins: {allowed_origins}")
            else:
                # 本番環境でALLOWED_ORIGINSが設定されていない場合はCORSを無効化
                self.logger.info("CORS disabled in production (no allowed origins)")
        else:
            # 開発・テスト環境: 緩いCORS設定
            CORS(self.app, origins="*")
            self.logger.info("CORS initialized with origins: *")
    
    def _init_security_headers(self):
        """セキュリティヘッダーの設定"""
        @self.app.after_request
        def add_security_headers(response: Response) -> Response:
            return self.apply_security_headers(response)
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """シークレットの取得"""
        try:
            if self.secrets_client and hasattr(self.secrets_client, 'get_secret_value'):
                # AWS Secrets Manager
                response = self.secrets_client.get_secret_value(SecretId=secret_name)
                return response['SecretString']
            elif self.secrets_client and hasattr(self.secrets_client, 'get_secret'):
                # Azure Key Vault
                secret = self.secrets_client.get_secret(secret_name)
                return secret.value
            else:
                # 環境変数フォールバック
                return os.getenv(secret_name)
        except Exception as e:
            self.logger.error(f"Failed to get secret {secret_name}: {e}")
            # フォールバック: 環境変数から取得
            return os.getenv(secret_name)
    
    def get_api_key(self, service_name: str) -> Optional[str]:
        """APIキーの取得"""
        key_mapping = {
            'gemini': 'GEMINI_API_KEY',
            'twitter': 'TWITTER_BEARER_TOKEN',
            'openai': 'OPENAI_API_KEY'
        }
        
        secret_name = key_mapping.get(service_name.lower())
        if not secret_name:
            self.logger.error(f"Unknown service: {service_name}")
            return None
        
        api_key = self.get_secret(secret_name)
        if not api_key:
            self.logger.error(f"API key not found for service: {service_name}")
        
        return api_key
    
    def validate_request(self, request) -> bool:
        """リクエストの検証"""
        # 基本的な検証ロジック
        if not request:
            return False
        
        # Content-Type検証（JSON APIの場合）
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('Content-Type', '')
            if content_type and 'application/json' not in content_type and request.get_json(silent=True) is not None:
                self.logger.warning(f"Invalid Content-Type: {content_type}")
                return False
        
        # User-Agent検証（ボット対策）
        user_agent = request.headers.get('User-Agent', '')
        if not user_agent or len(user_agent) < 10:
            self.logger.warning(f"Suspicious User-Agent: {user_agent}")
            return False
        
        return True
    
    def apply_security_headers(self, response: Response) -> Response:
        """セキュリティヘッダーの適用"""
        # HTTPS強制（本番環境）
        if os.getenv('ENVIRONMENT') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # XSS保護
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # CSP (Content Security Policy)
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self' https://api.twitter.com https://generativelanguage.googleapis.com"
        )
        response.headers['Content-Security-Policy'] = csp_policy
        
        # リファラーポリシー
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    def generate_secure_key(self, length: int = 32) -> str:
        """セキュアなキーの生成"""
        return secrets.token_urlsafe(length)
    
    def rate_limit_decorator(self, limit: str):
        """レート制限デコレータ"""
        if self.rate_limiter:
            return self.rate_limiter.limit(limit)
        else:
            # レート制限が無効な場合のダミーデコレータ
            def dummy_decorator(f):
                return f
            return dummy_decorator
    
    def create_error_response(self, error_code: int, message: str, details: Dict[str, Any] = None) -> Response:
        """エラーレスポンスの作成"""
        response_data = {
            'error': message,
            'code': error_code
        }
        
        if details:
            response_data['details'] = details
        
        response = jsonify(response_data)
        response.status_code = error_code
        
        return self.apply_security_headers(response)


# グローバルインスタンス
security_manager = SecurityManager()


def init_security(app: Flask) -> SecurityManager:
    """セキュリティマネージャーの初期化"""
    security_manager.init_app(app)
    return security_manager