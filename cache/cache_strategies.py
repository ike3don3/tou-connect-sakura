"""
CacheStrategies - キャッシュ戦略の実装
ユーザーデータ、分析結果、API応答の最適化されたキャッシュ戦略
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable
from functools import wraps

from cache.cache_manager import CacheManager


class UserDataCacheStrategy:
    """ユーザーデータキャッシュ戦略"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)
        self.strategy_name = 'user_data'
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """ユーザープロファイルの取得"""
        cache_key = f"user:{user_id}:profile"
        return self.cache.get(cache_key, cache_type=self.strategy_name)
    
    def set_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> bool:
        """ユーザープロファイルの設定"""
        cache_key = f"user:{user_id}:profile"
        return self.cache.set(cache_key, profile_data, cache_type=self.strategy_name)
    
    def get_user_interests(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """ユーザー興味の取得"""
        cache_key = f"user:{user_id}:interests"
        return self.cache.get(cache_key, cache_type=self.strategy_name)
    
    def set_user_interests(self, user_id: int, interests: List[Dict[str, Any]]) -> bool:
        """ユーザー興味の設定"""
        cache_key = f"user:{user_id}:interests"
        return self.cache.set(cache_key, interests, cache_type=self.strategy_name)
    
    def get_user_skills(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """ユーザースキルの取得"""
        cache_key = f"user:{user_id}:skills"
        return self.cache.get(cache_key, cache_type=self.strategy_name)
    
    def set_user_skills(self, user_id: int, skills: List[Dict[str, Any]]) -> bool:
        """ユーザースキルの設定"""
        cache_key = f"user:{user_id}:skills"
        return self.cache.set(cache_key, skills, cache_type=self.strategy_name)
    
    def invalidate_user_data(self, user_id: int) -> int:
        """ユーザーデータの無効化"""
        return self.cache.invalidate_user_cache(user_id)


class AnalysisResultsCacheStrategy:
    """分析結果キャッシュ戦略"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)
        self.strategy_name = 'analysis_results'
    
    def get_twitter_analysis(self, username: str) -> Optional[Dict[str, Any]]:
        """Twitter分析結果の取得"""
        cache_key = f"analysis:twitter:{username}"
        return self.cache.get(cache_key, cache_type=self.strategy_name)
    
    def set_twitter_analysis(self, username: str, analysis_data: Dict[str, Any]) -> bool:
        """Twitter分析結果の設定"""
        cache_key = f"analysis:twitter:{username}"
        # 分析結果には作成時刻を追加
        analysis_data['cached_at'] = datetime.now(timezone.utc).isoformat()
        return self.cache.set(cache_key, analysis_data, cache_type=self.strategy_name)
    
    def get_user_analysis(self, user_id: int) -> Optional[Dict[str, Any]]:
        """ユーザー分析結果の取得"""
        cache_key = f"analysis:user:{user_id}"
        return self.cache.get(cache_key, cache_type=self.strategy_name)
    
    def set_user_analysis(self, user_id: int, analysis_data: Dict[str, Any]) -> bool:
        """ユーザー分析結果の設定"""
        cache_key = f"analysis:user:{user_id}"
        analysis_data['cached_at'] = datetime.now(timezone.utc).isoformat()
        return self.cache.set(cache_key, analysis_data, cache_type=self.strategy_name)
    
    def get_gemini_analysis(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Gemini AI分析結果の取得"""
        cache_key = f"analysis:gemini:{content_hash}"
        return self.cache.get(cache_key, cache_type=self.strategy_name)
    
    def set_gemini_analysis(self, content_hash: str, analysis_data: Dict[str, Any]) -> bool:
        """Gemini AI分析結果の設定"""
        cache_key = f"analysis:gemini:{content_hash}"
        # AI分析結果は長期間キャッシュ（4時間）
        return self.cache.set(cache_key, analysis_data, ttl=14400, cache_type=self.strategy_name)
    
    def invalidate_analysis_cache(self, user_id: int = None, username: str = None) -> int:
        """分析結果キャッシュの無効化"""
        patterns = []
        
        if user_id:
            patterns.append(f"analysis:user:{user_id}:*")
        
        if username:
            patterns.append(f"analysis:twitter:{username}:*")
        
        total_deleted = 0
        for pattern in patterns:
            deleted = self.cache.clear_pattern(pattern)
            total_deleted += deleted
        
        return total_deleted


class MatchingResultsCacheStrategy:
    """マッチング結果キャッシュ戦略"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)
        self.strategy_name = 'matching_results'
    
    def get_user_matches(self, user_id: int, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
        """ユーザーマッチング結果の取得"""
        cache_key = f"match:user:{user_id}:limit:{limit}"
        return self.cache.get(cache_key)
    
    def set_user_matches(self, user_id: int, matches: List[Dict[str, Any]], limit: int = 5) -> bool:
        """ユーザーマッチング結果の設定"""
        cache_key = f"match:user:{user_id}:limit:{limit}"
        match_data = {
            'matches': matches,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'user_id': user_id,
            'limit': limit
        }
        return self.cache.set(cache_key, match_data, strategy=self.strategy_name)
    
    def get_similarity_scores(self, user_id1: int, user_id2: int) -> Optional[Dict[str, float]]:
        """類似度スコアの取得"""
        # ユーザーIDの順序を統一
        min_id, max_id = sorted([user_id1, user_id2])
        cache_key = f"match:similarity:{min_id}:{max_id}"
        return self.cache.get(cache_key)
    
    def set_similarity_scores(self, user_id1: int, user_id2: int, scores: Dict[str, float]) -> bool:
        """類似度スコアの設定"""
        min_id, max_id = sorted([user_id1, user_id2])
        cache_key = f"match:similarity:{min_id}:{max_id}"
        score_data = {
            'scores': scores,
            'calculated_at': datetime.now(timezone.utc).isoformat(),
            'user_ids': [min_id, max_id]
        }
        # 類似度スコアは長期間キャッシュ（6時間）
        return self.cache.set(cache_key, score_data, ttl=21600)
    
    def invalidate_matching_cache(self, user_id: int) -> int:
        """マッチングキャッシュの無効化"""
        patterns = [
            f"match:user:{user_id}:*",
            f"match:similarity:{user_id}:*",
            f"match:similarity:*:{user_id}:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = self.cache.clear_pattern(pattern)
            total_deleted += deleted
        
        return total_deleted


class APIResponseCacheStrategy:
    """API応答キャッシュ戦略"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)
        self.strategy_name = 'api_responses'
    
    def cached_api_response(self, ttl: int = 300):
        """API応答キャッシュデコレータ"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # リクエストパラメータからキャッシュキーを生成
                cache_key = self._generate_api_cache_key(func.__name__, args, kwargs)
                
                # キャッシュから取得を試行
                cached_response = self.cache.get(cache_key)
                if cached_response is not None:
                    self.logger.debug(f"API cache hit: {cache_key}")
                    return cached_response
                
                # API関数を実行
                response = func(*args, **kwargs)
                
                # 成功した応答のみキャッシュ
                if self._should_cache_response(response):
                    self.cache.set(cache_key, response, ttl=ttl)
                    self.logger.debug(f"API response cached: {cache_key}")
                
                return response
            return wrapper
        return decorator
    
    def get_twitter_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Twitter ユーザーデータの取得"""
        cache_key = f"api:twitter:user:{username}"
        return self.cache.get(cache_key)
    
    def set_twitter_user_data(self, username: str, user_data: Dict[str, Any]) -> bool:
        """Twitter ユーザーデータの設定"""
        cache_key = f"api:twitter:user:{username}"
        return self.cache.set(cache_key, user_data, strategy=self.strategy_name)
    
    def get_learning_resources(self, category: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """学習リソースの取得"""
        cache_key = f"api:resources:{category}:limit:{limit}"
        return self.cache.get(cache_key)
    
    def set_learning_resources(self, category: str, resources: List[Dict[str, Any]], limit: int = 10) -> bool:
        """学習リソースの設定"""
        cache_key = f"api:resources:{category}:limit:{limit}"
        resource_data = {
            'resources': resources,
            'category': category,
            'limit': limit,
            'cached_at': datetime.now(timezone.utc).isoformat()
        }
        # リソースデータは長期間キャッシュ（1時間）
        return self.cache.set(cache_key, resource_data, ttl=3600)
    
    def _generate_api_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """API キャッシュキーの生成"""
        import hashlib
        
        # 関数名とパラメータからハッシュを生成
        key_data = {
            'function': func_name,
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False, default=str)
        key_hash = hashlib.md5(key_str.encode('utf-8')).hexdigest()[:16]
        
        return f"api:{func_name}:{key_hash}"
    
    def _should_cache_response(self, response: Any) -> bool:
        """応答をキャッシュすべきかの判定"""
        # 辞書形式の応答の場合
        if isinstance(response, dict):
            # エラー応答はキャッシュしない
            if 'error' in response or 'status' in response and response['status'] == 'error':
                return False
            
            # 空の応答はキャッシュしない
            if not response or len(response) == 0:
                return False
        
        # リスト形式の応答の場合
        elif isinstance(response, list):
            # 空のリストはキャッシュしない
            if len(response) == 0:
                return False
        
        # その他の場合はキャッシュする
        return True


class SessionCacheStrategy:
    """セッションキャッシュ戦略"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)
        self.strategy_name = 'session_data'
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッションデータの取得"""
        cache_key = f"session:{session_id}"
        return self.cache.get(cache_key)
    
    def set_session_data(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """セッションデータの設定"""
        cache_key = f"session:{session_id}"
        session_data['last_accessed'] = datetime.now(timezone.utc).isoformat()
        return self.cache.set(cache_key, session_data, strategy=self.strategy_name)
    
    def update_session_data(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """セッションデータの更新"""
        current_data = self.get_session_data(session_id)
        if current_data:
            current_data.update(updates)
            return self.set_session_data(session_id, current_data)
        else:
            return self.set_session_data(session_id, updates)
    
    def delete_session(self, session_id: str) -> bool:
        """セッションの削除"""
        cache_key = f"session:{session_id}"
        return self.cache.delete(cache_key)
    
    def get_user_sessions(self, user_id: int) -> List[str]:
        """ユーザーのアクティブセッション一覧"""
        # 実装の簡略化のため、パターンマッチングは使用しない
        # 実際の実装では、セッション管理テーブルを使用することを推奨
        return []


class CacheStrategyManager:
    """キャッシュ戦略統合管理"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)
        
        # 各戦略の初期化
        self.user_data = UserDataCacheStrategy(cache_manager)
        self.analysis_results = AnalysisResultsCacheStrategy(cache_manager)
        self.matching_results = MatchingResultsCacheStrategy(cache_manager)
        self.api_responses = APIResponseCacheStrategy(cache_manager)
        self.session_data = SessionCacheStrategy(cache_manager)
    
    def invalidate_all_user_cache(self, user_id: int) -> Dict[str, int]:
        """ユーザー関連の全キャッシュを無効化"""
        results = {
            'user_data': self.user_data.invalidate_user_data(user_id),
            'analysis_results': self.analysis_results.invalidate_analysis_cache(user_id=user_id),
            'matching_results': self.matching_results.invalidate_matching_cache(user_id)
        }
        
        total_deleted = sum(results.values())
        self.logger.info(f"Invalidated {total_deleted} cache entries for user {user_id}")
        
        return results
    
    def warm_up_common_data(self) -> int:
        """共通データのウォームアップ"""
        def load_common_data():
            # 共通的にアクセスされるデータを事前にロード
            return {
                'static:categories': ['情報学', '経営学', '人文学'],
                'static:skills': ['Python', 'JavaScript', 'データ分析', 'マーケティング'],
                'static:interests': ['AI・機械学習', 'Web開発', 'データサイエンス', 'ビジネス戦略']
            }
        
        return self.cache.warm_up_cache(load_common_data)
    
    def get_cache_overview(self) -> Dict[str, Any]:
        """キャッシュ全体の概要"""
        stats = self.cache.get_stats()
        health = self.cache.health_check()
        
        return {
            'cache_stats': stats,
            'health_status': health,
            'strategies': {
                'user_data': {'ttl': 1800, 'description': 'ユーザープロファイル、興味、スキル'},
                'analysis_results': {'ttl': 7200, 'description': 'AI分析結果、Twitter分析'},
                'matching_results': {'ttl': 3600, 'description': 'マッチング結果、類似度スコア'},
                'api_responses': {'ttl': 300, 'description': 'API応答、外部データ'},
                'session_data': {'ttl': 86400, 'description': 'ユーザーセッション情報'}
            }
        }
    
    def cleanup_expired_cache(self) -> Dict[str, int]:
        """期限切れキャッシュのクリーンアップ"""
        # Redis の場合は自動的に期限切れキーが削除される
        # フォールバックキャッシュの場合は手動クリーンアップが必要
        
        if not self.cache.connected:
            # フォールバックキャッシュのクリーンアップ
            if hasattr(self.cache, 'fallback_expiry'):
                current_time = datetime.now(timezone.utc)
                expired_keys = [
                    key for key, expiry_time in self.cache.fallback_expiry.items()
                    if current_time > expiry_time
                ]
                
                cleaned_count = 0
                for key in expired_keys:
                    if self.cache._fallback_delete(key):
                        cleaned_count += 1
                
                return {'cleaned_keys': cleaned_count}
        
        return {'cleaned_keys': 0, 'message': 'Redis handles expiration automatically'}