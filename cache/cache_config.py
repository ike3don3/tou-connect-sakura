"""
キャッシュシステム設定
Redis接続設定とキャッシュ戦略の設定
"""

import os
from typing import Dict, Any

# Redis接続設定
REDIS_CONFIG = {
    "url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", "20")),
    "retry_on_timeout": True,
    "health_check_interval": 30,
    "socket_connect_timeout": 5,
    "socket_timeout": 5
}

# キャッシュ戦略設定
CACHE_STRATEGIES = {
    "user_data": {
        "ttl": 1800,  # 30分
        "prefix": "user:",
        "description": "ユーザープロファイル、興味、スキル情報"
    },
    "analysis_results": {
        "ttl": 7200,  # 2時間
        "prefix": "analysis:",
        "description": "AI分析結果、Twitter分析、マッチング結果"
    },
    "matching_results": {
        "ttl": 3600,  # 1時間
        "prefix": "match:",
        "description": "ユーザーマッチング結果"
    },
    "api_responses": {
        "ttl": 300,  # 5分
        "prefix": "api:",
        "description": "外部API応答結果"
    },
    "session_data": {
        "ttl": 86400,  # 24時間
        "prefix": "session:",
        "description": "ユーザーセッション情報"
    },
    "static_content": {
        "ttl": 86400,  # 24時間
        "prefix": "static:",
        "description": "静的コンテンツ、設定情報"
    }
}

# キャッシュモニタリング設定
CACHE_MONITORING = {
    "enable_stats": True,
    "stats_interval": 60,  # 統計収集間隔（秒）
    "enable_health_check": True,
    "health_check_interval": 30,  # ヘルスチェック間隔（秒）
    "alert_thresholds": {
        "hit_rate_min": 70,  # 最小ヒット率（%）
        "error_rate_max": 5,  # 最大エラー率（%）
        "response_time_max": 100  # 最大応答時間（ms）
    }
}

# 開発環境設定
DEV_CONFIG = {
    "redis_url": "redis://localhost:6379/1",  # 開発用DB
    "enable_debug_logging": True,
    "cache_ttl_multiplier": 0.1  # TTLを短縮（テスト用）
}

# 本番環境設定
PROD_CONFIG = {
    "redis_url": os.getenv("REDIS_URL", "redis://redis:6379/0"),
    "enable_debug_logging": False,
    "cache_ttl_multiplier": 1.0,
    "enable_persistence": True,
    "backup_interval": 3600  # 1時間ごとにバックアップ
}

def get_cache_config(environment: str = "development") -> Dict[str, Any]:
    """環境に応じたキャッシュ設定を取得"""
    base_config = {
        "redis": REDIS_CONFIG,
        "strategies": CACHE_STRATEGIES,
        "monitoring": CACHE_MONITORING
    }
    
    if environment == "production":
        base_config["redis"].update(PROD_CONFIG)
    else:
        base_config["redis"].update(DEV_CONFIG)
    
    return base_config

# キャッシュキー生成ヘルパー
class CacheKeyGenerator:
    """キャッシュキー生成ユーティリティ"""
    
    @staticmethod
    def user_profile(user_id: int) -> str:
        return f"user:{user_id}:profile"
    
    @staticmethod
    def user_interests(user_id: int) -> str:
        return f"user:{user_id}:interests"
    
    @staticmethod
    def user_skills(user_id: int) -> str:
        return f"user:{user_id}:skills"
    
    @staticmethod
    def twitter_analysis(username: str) -> str:
        return f"analysis:twitter:{username}"
    
    @staticmethod
    def user_analysis(user_id: int) -> str:
        return f"analysis:user:{user_id}"
    
    @staticmethod
    def gemini_analysis(content_hash: str) -> str:
        return f"analysis:gemini:{content_hash}"
    
    @staticmethod
    def matching_result(user_id1: int, user_id2: int) -> str:
        # IDの順序を統一
        min_id, max_id = min(user_id1, user_id2), max(user_id1, user_id2)
        return f"match:{min_id}:{max_id}"
    
    @staticmethod
    def api_response(endpoint: str, params_hash: str) -> str:
        return f"api:{endpoint}:{params_hash}"
    
    @staticmethod
    def session_data(session_id: str) -> str:
        return f"session:{session_id}"
