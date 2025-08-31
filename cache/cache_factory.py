"""
CacheFactory - キャッシュシステムファクトリー
アプリケーション全体でキャッシュシステムを統一的に管理
"""

import os
import logging
from typing import Optional, Dict, Any
from functools import lru_cache

from cache.cache_manager import CacheManager
from cache.cache_strategies import (
    UserDataCacheStrategy,
    AnalysisResultsCacheStrategy,
    # MatchingResultsCacheStrategy,  # 今後追加予定
    # APIResponseCacheStrategy      # 今後追加予定
)
from cache.cache_config import get_cache_config

class CacheFactory:
    """キャッシュシステムファクトリー"""
    
    _instance: Optional['CacheFactory'] = None
    _cache_manager: Optional[CacheManager] = None
    _strategies: Dict[str, Any] = {}
    
    def __new__(cls) -> 'CacheFactory':
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """ファクトリーの初期化"""
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self.logger = logging.getLogger(__name__)
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.config = get_cache_config(self.environment)
        
        # CacheManagerの初期化
        self._init_cache_manager()
        
        # キャッシュ戦略の初期化
        self._init_cache_strategies()
    
    def _init_cache_manager(self):
        """CacheManagerの初期化"""
        try:
            redis_url = self.config["redis"]["url"]
            self._cache_manager = CacheManager(
                redis_url=redis_url,
                monitoring_manager=None  # 必要に応じてモニタリングマネージャーを追加
            )
            
            # ヘルスチェック
            health = self._cache_manager.health_check()
            if health["status"] == "healthy":
                self.logger.info("Cache system initialized successfully")
            else:
                self.logger.warning(f"Cache system health check failed: {health}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize cache manager: {e}")
            self._cache_manager = None
    
    def _init_cache_strategies(self):
        """キャッシュ戦略の初期化"""
        if self._cache_manager is None:
            self.logger.warning("Cache manager not available, skipping strategy initialization")
            return
        
        try:
            # ユーザーデータキャッシュ戦略
            self._strategies["user_data"] = UserDataCacheStrategy(self._cache_manager)
            
            # 分析結果キャッシュ戦略
            self._strategies["analysis_results"] = AnalysisResultsCacheStrategy(self._cache_manager)
            
            # 今後追加予定の戦略
            # self._strategies["matching_results"] = MatchingResultsCacheStrategy(self._cache_manager)
            # self._strategies["api_responses"] = APIResponseCacheStrategy(self._cache_manager)
            
            self.logger.info(f"Initialized {len(self._strategies)} cache strategies")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize cache strategies: {e}")
    
    @property
    def cache_manager(self) -> Optional[CacheManager]:
        """CacheManagerインスタンスの取得"""
        return self._cache_manager
    
    @property
    def user_data_cache(self) -> Optional[UserDataCacheStrategy]:
        """ユーザーデータキャッシュ戦略の取得"""
        return self._strategies.get("user_data")
    
    @property
    def analysis_cache(self) -> Optional[AnalysisResultsCacheStrategy]:
        """分析結果キャッシュ戦略の取得"""
        return self._strategies.get("analysis_results")
    
    def get_strategy(self, strategy_name: str) -> Optional[Any]:
        """指定された名前のキャッシュ戦略を取得"""
        return self._strategies.get(strategy_name)
    
    def is_available(self) -> bool:
        """キャッシュシステムが利用可能かどうか"""
        return (self._cache_manager is not None and 
                self._cache_manager.connected)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """システム全体の統計情報を取得"""
        if not self.is_available():
            return {"status": "unavailable", "error": "Cache system not available"}
        
        try:
            stats = self._cache_manager.get_stats()
            health = self._cache_manager.health_check()
            
            return {
                "status": "available",
                "environment": self.environment,
                "cache_stats": stats,
                "health": health,
                "strategies": list(self._strategies.keys()),
                "config": {
                    "redis_url": self.config["redis"]["url"],
                    "strategies_count": len(self._strategies)
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to get system stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def clear_all_cache(self) -> bool:
        """全キャッシュのクリア"""
        if not self.is_available():
            return False
        
        try:
            result = self._cache_manager.clear_cache()
            if result:
                self.logger.info("All cache cleared successfully")
            return result
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            return False
    
    def clear_cache_by_type(self, cache_type: str) -> bool:
        """指定されたタイプのキャッシュをクリア"""
        if not self.is_available():
            return False
        
        try:
            result = self._cache_manager.clear_cache(cache_type)
            if result:
                self.logger.info(f"Cache type '{cache_type}' cleared successfully")
            return result
        except Exception as e:
            self.logger.error(f"Failed to clear cache type '{cache_type}': {e}")
            return False
    
    def shutdown(self):
        """キャッシュシステムのシャットダウン"""
        try:
            if self._cache_manager:
                # 必要に応じてクリーンアップ処理を追加
                self.logger.info("Cache system shutdown")
                
        except Exception as e:
            self.logger.error(f"Error during cache system shutdown: {e}")


# グローバルファクトリーインスタンス
@lru_cache(maxsize=1)
def get_cache_factory() -> CacheFactory:
    """CacheFactoryのシングルトンインスタンスを取得"""
    return CacheFactory()


# 便利な関数群
def get_cache_manager() -> Optional[CacheManager]:
    """CacheManagerインスタンスを取得"""
    factory = get_cache_factory()
    return factory.cache_manager


def get_user_data_cache() -> Optional[UserDataCacheStrategy]:
    """ユーザーデータキャッシュ戦略を取得"""
    factory = get_cache_factory()
    return factory.user_data_cache


def get_analysis_cache() -> Optional[AnalysisResultsCacheStrategy]:
    """分析結果キャッシュ戦略を取得"""
    factory = get_cache_factory()
    return factory.analysis_cache


def is_cache_available() -> bool:
    """キャッシュシステムが利用可能かどうか"""
    factory = get_cache_factory()
    return factory.is_available()


def get_cache_stats() -> Dict[str, Any]:
    """キャッシュシステムの統計情報を取得"""
    factory = get_cache_factory()
    return factory.get_system_stats()
