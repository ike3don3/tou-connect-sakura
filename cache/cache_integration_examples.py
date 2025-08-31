"""
キャッシュ機能統合サンプル
実際のアプリケーションでキャッシュを使用する例
"""

from functools import wraps
import hashlib
import json
import logging
from typing import Dict, Any, Optional

from cache.cache_factory import get_user_data_cache, get_analysis_cache, get_cache_manager

logger = logging.getLogger(__name__)


def cache_user_profile(cache_time: int = 1800):
    """ユーザープロファイルキャッシュデコレータ"""
    def decorator(func):
        @wraps(func)
        def wrapper(user_id: int, *args, **kwargs):
            user_cache = get_user_data_cache()
            
            # キャッシュが利用可能な場合
            if user_cache:
                # キャッシュから取得を試行
                cached_profile = user_cache.get_user_profile(user_id)
                if cached_profile:
                    logger.debug(f"User profile cache hit for user {user_id}")
                    return cached_profile
            
            # キャッシュミスまたはキャッシュ利用不可の場合、実際に処理実行
            result = func(user_id, *args, **kwargs)
            
            # 結果をキャッシュに保存
            if user_cache and result:
                user_cache.set_user_profile(user_id, result)
                logger.debug(f"User profile cached for user {user_id}")
            
            return result
        return wrapper
    return decorator


def cache_analysis_result(cache_time: int = 7200):
    """分析結果キャッシュデコレータ"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            analysis_cache = get_analysis_cache()
            
            # キャッシュキーの生成
            cache_key_data = {
                "func": func.__name__,
                "args": str(args),
                "kwargs": str(sorted(kwargs.items()))
            }
            cache_key = hashlib.md5(json.dumps(cache_key_data, sort_keys=True).encode()).hexdigest()
            
            # キャッシュが利用可能な場合
            if analysis_cache:
                cache_manager = get_cache_manager()
                if cache_manager:
                    # キャッシュから取得を試行
                    cached_result = cache_manager.get(cache_key, cache_type="analysis_results")
                    if cached_result:
                        logger.debug(f"Analysis result cache hit for key {cache_key}")
                        return cached_result
            
            # キャッシュミスまたはキャッシュ利用不可の場合、実際に処理実行
            result = func(*args, **kwargs)
            
            # 結果をキャッシュに保存
            if analysis_cache and result:
                cache_manager = get_cache_manager()
                if cache_manager:
                    cache_manager.set(cache_key, result, ttl=cache_time, cache_type="analysis_results")
                    logger.debug(f"Analysis result cached with key {cache_key}")
            
            return result
        return wrapper
    return decorator


class CachedUserService:
    """キャッシュ機能付きユーザーサービス"""
    
    def __init__(self, user_repository):
        self.user_repo = user_repository
        self.user_cache = get_user_data_cache()
        self.logger = logging.getLogger(__name__)
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """キャッシュ機能付きユーザープロファイル取得"""
        if self.user_cache:
            # キャッシュから取得を試行
            cached_profile = self.user_cache.get_user_profile(user_id)
            if cached_profile:
                self.logger.debug(f"User profile cache hit for user {user_id}")
                return cached_profile
        
        # データベースから取得
        profile = self.user_repo.get_user_by_id(user_id)
        
        # キャッシュに保存
        if self.user_cache and profile:
            self.user_cache.set_user_profile(user_id, profile)
            self.logger.debug(f"User profile cached for user {user_id}")
        
        return profile
    
    def get_user_interests(self, user_id: int) -> Optional[list]:
        """キャッシュ機能付きユーザー興味取得"""
        if self.user_cache:
            cached_interests = self.user_cache.get_user_interests(user_id)
            if cached_interests:
                self.logger.debug(f"User interests cache hit for user {user_id}")
                return cached_interests
        
        # データベースから取得（実際の実装では適切なリポジトリメソッドを使用）
        interests = self.user_repo.get_user_interests(user_id) if hasattr(self.user_repo, 'get_user_interests') else []
        
        if self.user_cache and interests:
            self.user_cache.set_user_interests(user_id, interests)
            self.logger.debug(f"User interests cached for user {user_id}")
        
        return interests
    
    def get_user_skills(self, user_id: int) -> Optional[list]:
        """キャッシュ機能付きユーザースキル取得"""
        if self.user_cache:
            cached_skills = self.user_cache.get_user_skills(user_id)
            if cached_skills:
                self.logger.debug(f"User skills cache hit for user {user_id}")
                return cached_skills
        
        # データベースから取得（実際の実装では適切なリポジトリメソッドを使用）
        skills = self.user_repo.get_user_skills(user_id) if hasattr(self.user_repo, 'get_user_skills') else []
        
        if self.user_cache and skills:
            self.user_cache.set_user_skills(user_id, skills)
            self.logger.debug(f"User skills cached for user {user_id}")
        
        return skills
    
    def invalidate_user_cache(self, user_id: int):
        """ユーザーキャッシュの無効化"""
        if self.user_cache:
            cache_manager = get_cache_manager()
            if cache_manager:
                # 関連するキャッシュを削除
                cache_manager.delete(f"user:{user_id}:profile", cache_type="user_data")
                cache_manager.delete(f"user:{user_id}:interests", cache_type="user_data")
                cache_manager.delete(f"user:{user_id}:skills", cache_type="user_data")
                self.logger.info(f"User cache invalidated for user {user_id}")


class CachedAnalysisService:
    """キャッシュ機能付き分析サービス"""
    
    def __init__(self, analysis_repository):
        self.analysis_repo = analysis_repository
        self.analysis_cache = get_analysis_cache()
        self.logger = logging.getLogger(__name__)
    
    def get_twitter_analysis(self, username: str) -> Optional[Dict[str, Any]]:
        """キャッシュ機能付きTwitter分析取得"""
        if self.analysis_cache:
            cached_analysis = self.analysis_cache.get_twitter_analysis(username)
            if cached_analysis:
                self.logger.debug(f"Twitter analysis cache hit for {username}")
                return cached_analysis
        
        # 実際の分析を実行（重い処理）
        analysis = self._perform_twitter_analysis(username)
        
        # 結果をキャッシュに保存
        if self.analysis_cache and analysis:
            self.analysis_cache.set_twitter_analysis(username, analysis)
            self.logger.debug(f"Twitter analysis cached for {username}")
        
        return analysis
    
    def get_user_analysis(self, user_id: int) -> Optional[Dict[str, Any]]:
        """キャッシュ機能付きユーザー分析取得"""
        if self.analysis_cache:
            cached_analysis = self.analysis_cache.get_user_analysis(user_id)
            if cached_analysis:
                self.logger.debug(f"User analysis cache hit for user {user_id}")
                return cached_analysis
        
        # 実際の分析を実行
        analysis = self._perform_user_analysis(user_id)
        
        # 結果をキャッシュに保存
        if self.analysis_cache and analysis:
            self.analysis_cache.set_user_analysis(user_id, analysis)
            self.logger.debug(f"User analysis cached for user {user_id}")
        
        return analysis
    
    @cache_analysis_result(cache_time=14400)  # 4時間キャッシュ
    def get_gemini_analysis(self, content: str) -> Optional[Dict[str, Any]]:
        """キャッシュ機能付きGemini AI分析"""
        # コンテンツのハッシュを生成
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # 実際のGemini分析を実行（重い処理）
        analysis = self._perform_gemini_analysis(content, content_hash)
        
        return analysis
    
    def _perform_twitter_analysis(self, username: str) -> Dict[str, Any]:
        """実際のTwitter分析処理（プレースホルダー）"""
        # 実際の実装では Twitter API や分析ロジックを使用
        return {
            "username": username,
            "analysis": "placeholder_twitter_analysis",
            "timestamp": "2025-08-19T20:15:00Z"
        }
    
    def _perform_user_analysis(self, user_id: int) -> Dict[str, Any]:
        """実際のユーザー分析処理（プレースホルダー）"""
        # 実際の実装では AI 分析や統計処理を使用
        return {
            "user_id": user_id,
            "analysis": "placeholder_user_analysis",
            "timestamp": "2025-08-19T20:15:00Z"
        }
    
    def _perform_gemini_analysis(self, content: str, content_hash: str) -> Dict[str, Any]:
        """実際のGemini AI分析処理（プレースホルダー）"""
        # 実際の実装では Gemini API を使用
        return {
            "content_hash": content_hash,
            "analysis": "placeholder_gemini_analysis",
            "content_length": len(content),
            "timestamp": "2025-08-19T20:15:00Z"
        }


# 使用例関数
def example_usage():
    """キャッシュ機能の使用例"""
    
    # デコレータを使用した例
    @cache_user_profile(cache_time=1800)
    def get_user_profile_with_cache(user_id: int):
        # 実際のデータベース処理
        return {"user_id": user_id, "name": f"User {user_id}"}
    
    @cache_analysis_result(cache_time=3600)
    def expensive_analysis(data: str):
        # 重い分析処理のシミュレーション
        import time
        time.sleep(1)  # 1秒の処理時間をシミュレート
        return {"result": f"analysis of {data}", "processing_time": 1}
    
    # 使用例
    profile = get_user_profile_with_cache(123)
    analysis = expensive_analysis("sample data")
    
    return profile, analysis
