"""
CacheManager - Redis キャッシュ管理システム
ユーザーデータ、分析結果、セッション情報のキャッシュ管理
"""

import os
import json
import time
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
import pickle

try:
    import redis
    from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

class CacheManager:
    """Redis キャッシュ管理システム"""
    
    def __init__(self, redis_url: str = None, monitoring_manager=None):
        self.monitoring_manager = monitoring_manager
        self.logger = logging.getLogger(__name__)
        
        # Redis設定
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = None
        self.connected = False
        
        # キャッシュ設定
        self.default_ttl = 3600  # 1時間
        self.key_prefix = "tou_connect:"
        
        # キャッシュ戦略設定
        self.cache_strategies = {
            "user_data": {"ttl": 1800, "prefix": "user:"},        # 30分
            "analysis_results": {"ttl": 7200, "prefix": "analysis:"},  # 2時間
            "matching_results": {"ttl": 3600, "prefix": "match:"},     # 1時間
            "api_responses": {"ttl": 300, "prefix": "api:"},           # 5分
            "session_data": {"ttl": 86400, "prefix": "session:"},     # 24時間
            "static_content": {"ttl": 86400, "prefix": "static:"}     # 24時間
        }
        
        # 統計情報
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
            "total_keys": 0
        }
        
        # 初期化
        self._init_cache()
        
    def _init_cache(self):
        """キャッシュシステムの初期化"""
        if not REDIS_AVAILABLE:
            self.logger.warning("Redis not available, using in-memory cache")
            return False
            
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            self.connected = True
            self.logger.info("Redis connection established")
            return True
        except Exception as e:
            self.logger.error(f"Redis connection failed: {e}")
            self.connected = False
            return False
    
    def _get_cache_key(self, key: str, cache_type: str = "default") -> str:
        """キャッシュキーの生成"""
        if cache_type in self.cache_strategies:
            prefix = self.cache_strategies[cache_type]["prefix"]
        else:
            prefix = ""
        return f"{self.key_prefix}{prefix}{key}"
    
    def _get_ttl(self, cache_type: str = "default") -> int:
        """TTL値の取得"""
        if cache_type in self.cache_strategies:
            return self.cache_strategies[cache_type]["ttl"]
        return self.default_ttl
    
    def set(self, key: str, value: Any, ttl: int = None, cache_type: str = "default") -> bool:
        """値をキャッシュに保存"""
        if not self.connected:
            return False
            
        try:
            cache_key = self._get_cache_key(key, cache_type)
            cache_ttl = ttl or self._get_ttl(cache_type)
            
            # 値をJSONまたはPickleでシリアライズ
            try:
                serialized_value = json.dumps(value)
            except (TypeError, ValueError):
                serialized_value = pickle.dumps(value).hex()
                cache_key += ":pickle"
            
            result = self.redis_client.setex(cache_key, cache_ttl, serialized_value)
            
            if result:
                self.stats["sets"] += 1
                self.logger.debug(f"Cache set: {cache_key}")
                
                # モニタリング
                if self.monitoring_manager:
                    self.monitoring_manager.log_cache_operation("set", cache_type, True)
                    
            return result
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Cache set error: {e}")
            if self.monitoring_manager:
                self.monitoring_manager.log_cache_operation("set", cache_type, False, str(e))
            return False
    
    def get(self, key: str, cache_type: str = "default") -> Optional[Any]:
        """キャッシュから値を取得"""
        if not self.connected:
            return None
            
        try:
            cache_key = self._get_cache_key(key, cache_type)
            
            # Pickleバージョンも確認
            pickle_key = cache_key + ":pickle"
            
            # まずJSON版を試す
            value = self.redis_client.get(cache_key)
            is_pickle = False
            
            if value is None:
                # Pickle版を試す
                value = self.redis_client.get(pickle_key)
                is_pickle = True
            
            if value is not None:
                self.stats["hits"] += 1
                self.logger.debug(f"Cache hit: {cache_key}")
                
                # デシリアライズ
                try:
                    if is_pickle:
                        return pickle.loads(bytes.fromhex(value))
                    else:
                        return json.loads(value)
                except Exception as e:
                    self.logger.error(f"Cache deserialization error: {e}")
                    # 破損したキャッシュを削除
                    self.delete(key, cache_type)
                    return None
                    
                # モニタリング
                if self.monitoring_manager:
                    self.monitoring_manager.log_cache_operation("get", cache_type, True)
                    
            else:
                self.stats["misses"] += 1
                self.logger.debug(f"Cache miss: {cache_key}")
                
                if self.monitoring_manager:
                    self.monitoring_manager.log_cache_operation("get", cache_type, False)
                    
            return None if value is None else value
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Cache get error: {e}")
            if self.monitoring_manager:
                self.monitoring_manager.log_cache_operation("get", cache_type, False, str(e))
            return None
    
    def delete(self, key: str, cache_type: str = "default") -> bool:
        """キャッシュから値を削除"""
        if not self.connected:
            return False
            
        try:
            cache_key = self._get_cache_key(key, cache_type)
            pickle_key = cache_key + ":pickle"
            
            # 両方のバージョンを削除
            result1 = self.redis_client.delete(cache_key)
            result2 = self.redis_client.delete(pickle_key)
            
            success = result1 > 0 or result2 > 0
            
            if success:
                self.stats["deletes"] += 1
                self.logger.debug(f"Cache deleted: {cache_key}")
                
                if self.monitoring_manager:
                    self.monitoring_manager.log_cache_operation("delete", cache_type, True)
                    
            return success
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Cache delete error: {e}")
            if self.monitoring_manager:
                self.monitoring_manager.log_cache_operation("delete", cache_type, False, str(e))
            return False
    
    def exists(self, key: str, cache_type: str = "default") -> bool:
        """キーの存在確認"""
        if not self.connected:
            return False
            
        try:
            cache_key = self._get_cache_key(key, cache_type)
            pickle_key = cache_key + ":pickle"
            
            return (self.redis_client.exists(cache_key) or 
                   self.redis_client.exists(pickle_key))
                   
        except Exception as e:
            self.logger.error(f"Cache exists error: {e}")
            return False
    
    def clear_cache(self, cache_type: str = None) -> bool:
        """キャッシュのクリア"""
        if not self.connected:
            return False
            
        try:
            if cache_type:
                # 特定のタイプのキャッシュをクリア
                prefix = self.cache_strategies.get(cache_type, {}).get("prefix", "")
                pattern = f"{self.key_prefix}{prefix}*"
                keys = self.redis_client.keys(pattern)
                
                if keys:
                    self.redis_client.delete(*keys)
                    self.logger.info(f"Cleared {len(keys)} keys for cache type: {cache_type}")
                    
            else:
                # 全てのキャッシュをクリア
                keys = self.redis_client.keys(f"{self.key_prefix}*")
                if keys:
                    self.redis_client.delete(*keys)
                    self.logger.info(f"Cleared all cache: {len(keys)} keys")
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計の取得"""
        try:
            if self.connected:
                info = self.redis_client.info()
                self.stats.update({
                    "redis_used_memory": info.get("used_memory_human", "N/A"),
                    "redis_connected_clients": info.get("connected_clients", 0),
                    "redis_total_commands": info.get("total_commands_processed", 0),
                    "total_keys": self.redis_client.dbsize()
                })
        except Exception as e:
            self.logger.error(f"Stats error: {e}")
            
        # ヒット率の計算
        total_gets = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_gets * 100) if total_gets > 0 else 0
        
        return {
            **self.stats,
            "hit_rate": round(hit_rate, 2),
            "connected": self.connected,
            "redis_available": REDIS_AVAILABLE
        }
    
    def cache_decorator(self, cache_type: str = "default", ttl: int = None):
        """キャッシュデコレータ"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # キャッシュキーの生成
                key_data = {
                    "func": func.__name__,
                    "args": str(args),
                    "kwargs": str(sorted(kwargs.items()))
                }
                cache_key = hashlib.md5(str(key_data).encode()).hexdigest()
                
                # キャッシュから取得を試行
                cached_result = self.get(cache_key, cache_type)
                if cached_result is not None:
                    return cached_result
                
                # 関数実行とキャッシュ保存
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl, cache_type)
                
                return result
            
            return wrapper
        return decorator
    
    def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        health = {
            "status": "healthy",
            "redis_connected": self.connected,
            "redis_available": REDIS_AVAILABLE,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if self.connected:
            try:
                # Redis接続テスト
                start_time = time.time()
                self.redis_client.ping()
                response_time = (time.time() - start_time) * 1000
                
                health.update({
                    "redis_response_time_ms": round(response_time, 2),
                    "redis_info": {
                        "version": self.redis_client.info().get("redis_version", "unknown"),
                        "uptime": self.redis_client.info().get("uptime_in_seconds", 0)
                    }
                })
                
            except Exception as e:
                health.update({
                    "status": "degraded",
                    "redis_error": str(e)
                })
        else:
            health["status"] = "degraded"
            
        return health
