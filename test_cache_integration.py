#!/usr/bin/env python3
"""
キャッシュシステム統合テスト
改良されたCacheManagerとCacheStrategiesの動作確認
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cache.cache_manager import CacheManager
from cache.cache_strategies import UserDataCacheStrategy, AnalysisResultsCacheStrategy

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_cache_manager_basic():
    """CacheManagerの基本機能テスト"""
    logger.info("=== CacheManager基本機能テスト ===")
    
    # CacheManagerの初期化
    cache = CacheManager()
    
    # ヘルスチェック
    health = cache.health_check()
    logger.info(f"Health check: {health}")
    
    # 基本的なset/get操作
    test_key = "test_key"
    test_value = {"message": "Hello, World!", "timestamp": datetime.now().isoformat()}
    
    if cache.connected:
        # 値の設定
        success = cache.set(test_key, test_value, cache_type="api_responses")
        logger.info(f"Set operation success: {success}")
        
        # 値の取得
        retrieved_value = cache.get(test_key, cache_type="api_responses")
        logger.info(f"Retrieved value: {retrieved_value}")
        
        # 存在確認
        exists = cache.exists(test_key, cache_type="api_responses")
        logger.info(f"Key exists: {exists}")
    else:
        logger.info("Redis not available, skipping cache operations")
    
    # 統計情報
    stats = cache.get_stats()
    logger.info(f"Cache stats: {stats}")
    
    return cache

def test_cache_decorator():
    """キャッシュデコレータのテスト"""
    logger.info("=== キャッシュデコレータテスト ===")
    
    cache = CacheManager()
    
    @cache.cache_decorator(cache_type="analysis_results", ttl=300)
    def expensive_calculation(x, y):
        """重い計算をシミュレート"""
        time.sleep(0.1)  # 計算時間をシミュレート
        result = x * y + (x ** 2) + (y ** 2)
        logger.info(f"Expensive calculation executed: {x} * {y} = {result}")
        return result
    
    # 初回実行（キャッシュミス）
    start_time = time.time()
    result1 = expensive_calculation(5, 10)
    time1 = time.time() - start_time
    logger.info(f"First call result: {result1}, time: {time1:.3f}s")
    
    # 2回目実行（キャッシュヒット）
    start_time = time.time()
    result2 = expensive_calculation(5, 10)
    time2 = time.time() - start_time
    logger.info(f"Second call result: {result2}, time: {time2:.3f}s")
    
    # 結果が同じことを確認
    assert result1 == result2, "Results should be identical"
    
    # Redisが利用可能な場合のみ速度テスト
    if cache.connected:
        assert time2 < time1, "Second call should be faster (cached)"
        logger.info("キャッシュによる高速化を確認")
    else:
        logger.info("Redis not available, skipping performance test")
    
    logger.info("デコレータテスト成功")

def test_user_data_cache_strategy():
    """UserDataCacheStrategyのテスト"""
    logger.info("=== UserDataCacheStrategy テスト ===")
    
    cache = CacheManager()
    user_cache = UserDataCacheStrategy(cache)
    
    if not cache.connected:
        logger.info("Redis not available, skipping user data cache tests")
        return
    
    user_id = 12345
    
    # ユーザープロファイルデータ
    profile_data = {
        "user_id": user_id,
        "username": "test_user",
        "display_name": "Test User",
        "bio": "This is a test user profile",
        "location": "Tokyo, Japan",
        "created_at": datetime.now().isoformat()
    }
    
    # プロファイルの保存
    success = user_cache.set_user_profile(user_id, profile_data)
    logger.info(f"Profile save success: {success}")
    
    # プロファイルの取得
    retrieved_profile = user_cache.get_user_profile(user_id)
    logger.info(f"Retrieved profile: {retrieved_profile}")
    
    # 興味データ
    interests_data = [
        {"category": "technology", "keywords": ["AI", "Machine Learning", "Python"]},
        {"category": "sports", "keywords": ["football", "basketball"]},
        {"category": "music", "keywords": ["jazz", "classical"]}
    ]
    
    # 興味の保存と取得
    user_cache.set_user_interests(user_id, interests_data)
    retrieved_interests = user_cache.get_user_interests(user_id)
    logger.info(f"Retrieved interests: {retrieved_interests}")
    
    # スキルデータ
    skills_data = [
        {"skill": "Python", "level": "advanced", "years": 5},
        {"skill": "JavaScript", "level": "intermediate", "years": 3},
        {"skill": "SQL", "level": "advanced", "years": 4}
    ]
    
    # スキルの保存と取得
    user_cache.set_user_skills(user_id, skills_data)
    retrieved_skills = user_cache.get_user_skills(user_id)
    logger.info(f"Retrieved skills: {retrieved_skills}")

def test_analysis_results_cache_strategy():
    """AnalysisResultsCacheStrategyのテスト"""
    logger.info("=== AnalysisResultsCacheStrategy テスト ===")
    
    cache = CacheManager()
    analysis_cache = AnalysisResultsCacheStrategy(cache)
    
    if not cache.connected:
        logger.info("Redis not available, skipping analysis cache tests")
        return
    
    # Twitter分析結果
    twitter_username = "test_twitter_user"
    twitter_analysis = {
        "username": twitter_username,
        "follower_count": 1500,
        "following_count": 300,
        "tweet_count": 850,
        "interests": ["technology", "programming", "AI"],
        "sentiment_score": 0.75,
        "engagement_rate": 0.05,
        "analyzed_at": datetime.now().isoformat()
    }
    
    # Twitter分析結果の保存と取得
    analysis_cache.set_twitter_analysis(twitter_username, twitter_analysis)
    retrieved_twitter = analysis_cache.get_twitter_analysis(twitter_username)
    logger.info(f"Retrieved Twitter analysis: {retrieved_twitter}")
    
    # ユーザー分析結果
    user_id = 67890
    user_analysis = {
        "user_id": user_id,
        "personality_traits": {
            "openness": 0.8,
            "conscientiousness": 0.7,
            "extraversion": 0.6,
            "agreeableness": 0.75,
            "neuroticism": 0.3
        },
        "interests_match_score": 0.85,
        "skills_compatibility": 0.78,
        "communication_style": "collaborative",
        "analyzed_at": datetime.now().isoformat()
    }
    
    # ユーザー分析結果の保存と取得
    analysis_cache.set_user_analysis(user_id, user_analysis)
    retrieved_analysis = analysis_cache.get_user_analysis(user_id)
    logger.info(f"Retrieved user analysis: {retrieved_analysis}")
    
    # Gemini AI分析結果
    content_hash = "abc123def456"
    gemini_analysis = {
        "content_hash": content_hash,
        "topics": ["artificial intelligence", "machine learning", "data science"],
        "sentiment": "positive",
        "complexity_score": 0.7,
        "relevance_score": 0.9,
        "generated_at": datetime.now().isoformat()
    }
    
    # Gemini分析結果の保存と取得
    analysis_cache.set_gemini_analysis(content_hash, gemini_analysis)
    retrieved_gemini = analysis_cache.get_gemini_analysis(content_hash)
    logger.info(f"Retrieved Gemini analysis: {retrieved_gemini}")

def test_cache_performance():
    """キャッシュパフォーマンステスト"""
    logger.info("=== キャッシュパフォーマンステスト ===")
    
    cache = CacheManager()
    
    if not cache.connected:
        logger.info("Redis not available, skipping performance tests")
        return
    
    # 大量データの保存テスト
    num_operations = 100
    large_data = {
        "data": list(range(1000)),
        "metadata": {"size": 1000, "type": "performance_test"}
    }
    
    # 書き込み性能テスト
    start_time = time.time()
    for i in range(num_operations):
        cache.set(f"perf_test_key_{i}", large_data, cache_type="static_content")
    write_time = time.time() - start_time
    
    # 読み込み性能テスト
    start_time = time.time()
    for i in range(num_operations):
        result = cache.get(f"perf_test_key_{i}", cache_type="static_content")
    read_time = time.time() - start_time
    
    logger.info(f"Write performance: {num_operations} operations in {write_time:.3f}s ({num_operations/write_time:.1f} ops/s)")
    logger.info(f"Read performance: {num_operations} operations in {read_time:.3f}s ({num_operations/read_time:.1f} ops/s)")
    
    # 統計情報の表示
    stats = cache.get_stats()
    logger.info(f"Final cache stats: {stats}")

def test_cache_cleanup():
    """キャッシュクリーンアップテスト"""
    logger.info("=== キャッシュクリーンアップテスト ===")
    
    cache = CacheManager()
    
    if not cache.connected:
        logger.info("Redis not available, skipping cleanup tests")
        return
    
    # テストデータの追加
    for i in range(10):
        cache.set(f"cleanup_test_{i}", {"data": i}, cache_type="api_responses")
    
    # 特定タイプのキャッシュクリア
    success = cache.clear_cache("api_responses")
    logger.info(f"Cache cleanup success: {success}")
    
    # クリア後の確認
    for i in range(10):
        exists = cache.exists(f"cleanup_test_{i}", cache_type="api_responses")
        if exists:
            logger.error(f"Key cleanup_test_{i} still exists after cleanup")
    
    logger.info("クリーンアップテスト完了")

def main():
    """メインテスト実行"""
    logger.info("キャッシュシステム統合テスト開始")
    
    try:
        # 基本機能テスト
        cache = test_cache_manager_basic()
        
        # デコレータテスト
        test_cache_decorator()
        
        # ユーザーデータキャッシュテスト
        test_user_data_cache_strategy()
        
        # 分析結果キャッシュテスト
        test_analysis_results_cache_strategy()
        
        # パフォーマンステスト
        test_cache_performance()
        
        # クリーンアップテスト
        test_cache_cleanup()
        
        logger.info("全てのテストが正常に完了しました")
        
    except Exception as e:
        logger.error(f"テスト実行中にエラーが発生しました: {e}")
        raise

if __name__ == "__main__":
    main()
