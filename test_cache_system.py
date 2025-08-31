#!/usr/bin/env python3
"""
キャッシュシステムのテスト
CacheManagerとCacheStrategiesの機能テスト
"""
import os
import sys
import time
import json
from datetime import datetime, timezone

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cache.cache_manager import CacheManager
from cache.cache_strategies import CacheStrategyManager
from monitoring.monitoring_manager import MonitoringManager
from database.database_manager import DatabaseManager


def test_cache_manager():
    """CacheManagerの基本機能テスト"""
    print("=== CacheManager基本機能テスト ===")
    
    # MonitoringManagerの初期化
    db = DatabaseManager()
    monitoring = MonitoringManager(db)
    
    # CacheManagerの初期化（Redisが利用できない場合はフォールバック）
    cache = CacheManager(monitoring_manager=monitoring)
    
    try:
        # 1. 基本的なget/set操作
        print("1. 基本的なget/set操作")
        
        # 文字列データ
        cache.set("test:string", "Hello, World!")
        result = cache.get("test:string")
        assert result == "Hello, World!", f"Expected 'Hello, World!', got {result}"
        print("✓ 文字列データの保存・取得成功")
        
        # 数値データ
        cache.set("test:number", 42)
        result = cache.get("test:number")
        assert result == 42, f"Expected 42, got {result}"
        print("✓ 数値データの保存・取得成功")
        
        # 辞書データ
        test_dict = {"name": "太郎", "age": 25, "skills": ["Python", "JavaScript"]}
        cache.set("test:dict", test_dict)
        result = cache.get("test:dict")
        assert result == test_dict, f"Expected {test_dict}, got {result}"
        print("✓ 辞書データの保存・取得成功")
        
        # 2. TTL（有効期限）テスト
        print("2. TTL（有効期限）テスト")
        
        cache.set("test:ttl", "expires_soon", ttl=2)  # 2秒で期限切れ
        result = cache.get("test:ttl")
        assert result == "expires_soon", "TTL設定直後の取得に失敗"
        print("✓ TTL設定直後の取得成功")
        
        time.sleep(3)  # 3秒待機
        result = cache.get("test:ttl", "default_value")
        
        # Redis使用時は期限切れで削除、フォールバック時は期限チェック
        if cache.connected:
            assert result == "default_value", "TTL期限切れ後のデフォルト値取得に失敗"
        print("✓ TTL期限切れ処理成功")
        
        # 3. 存在確認テスト
        print("3. 存在確認テスト")
        
        cache.set("test:exists", "I exist")
        assert cache.exists("test:exists"), "存在するキーの確認に失敗"
        assert not cache.exists("test:not_exists"), "存在しないキーの確認に失敗"
        print("✓ 存在確認機能成功")
        
        # 4. 削除テスト
        print("4. 削除テスト")
        
        cache.set("test:delete", "delete_me")
        assert cache.exists("test:delete"), "削除前の存在確認に失敗"
        
        success = cache.delete("test:delete")
        assert success, "削除操作に失敗"
        assert not cache.exists("test:delete"), "削除後の存在確認に失敗"
        print("✓ 削除機能成功")
        
        # 5. パターン削除テスト
        print("5. パターン削除テスト")
        
        # 複数のキーを設定
        cache.set("pattern:test:1", "value1")
        cache.set("pattern:test:2", "value2")
        cache.set("pattern:other:1", "other1")
        
        # パターンマッチで削除
        deleted_count = cache.clear_pattern("pattern:test:*")
        
        # 結果確認
        assert not cache.exists("pattern:test:1"), "パターン削除後の確認1に失敗"
        assert not cache.exists("pattern:test:2"), "パターン削除後の確認2に失敗"
        assert cache.exists("pattern:other:1"), "パターン削除で関係ないキーが削除された"
        
        print(f"✓ パターン削除機能成功: {deleted_count} keys deleted")
        
        # 6. 統計情報テスト
        print("6. 統計情報テスト")
        
        stats = cache.get_stats()
        assert 'hits' in stats, "統計情報にhitsが含まれていない"
        assert 'misses' in stats, "統計情報にmissesが含まれていない"
        assert 'sets' in stats, "統計情報にsetsが含まれていない"
        
        print(f"✓ 統計情報取得成功:")
        print(f"  - Hits: {stats['hits']}")
        print(f"  - Misses: {stats['misses']}")
        print(f"  - Sets: {stats['sets']}")
        print(f"  - Hit Rate: {stats['hit_rate']:.1f}%")
        
        # 7. ヘルスチェックテスト
        print("7. ヘルスチェックテスト")
        
        health = cache.health_check()
        assert 'status' in health, "ヘルスチェック結果にstatusが含まれていない"
        
        print(f"✓ ヘルスチェック成功:")
        print(f"  - Status: {health['status']}")
        print(f"  - Connected: {health.get('connected', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ CacheManagerテストエラー: {e}")
        return False
    
    finally:
        # クリーンアップ
        monitoring.stop_background_tasks()


def test_cache_strategies():
    """CacheStrategiesの機能テスト"""
    print("\n=== CacheStrategies機能テスト ===")
    
    # MonitoringManagerの初期化
    db = DatabaseManager()
    monitoring = MonitoringManager(db)
    
    # CacheManagerとStrategiesの初期化
    cache = CacheManager(monitoring_manager=monitoring)
    strategies = CacheStrategyManager(cache)
    
    try:
        # 1. ユーザーデータキャッシュテスト
        print("1. ユーザーデータキャッシュテスト")
        
        user_id = 123
        profile_data = {
            "name": "田中太郎",
            "email": "tanaka@example.com",
            "university": "東京通信大学",
            "major": "情報学"
        }
        
        # プロファイル設定・取得
        success = strategies.user_data.set_user_profile(user_id, profile_data)
        assert success, "ユーザープロファイル設定に失敗"
        
        cached_profile = strategies.user_data.get_user_profile(user_id)
        assert cached_profile == profile_data, "ユーザープロファイル取得に失敗"
        print("✓ ユーザープロファイルキャッシュ成功")
        
        # 興味・スキル設定・取得
        interests = [
            {"category": "AI・機械学習", "level": 3},
            {"category": "Web開発", "level": 4}
        ]
        skills = [
            {"name": "Python", "level": 4},
            {"name": "JavaScript", "level": 3}
        ]
        
        strategies.user_data.set_user_interests(user_id, interests)
        strategies.user_data.set_user_skills(user_id, skills)
        
        cached_interests = strategies.user_data.get_user_interests(user_id)
        cached_skills = strategies.user_data.get_user_skills(user_id)
        
        assert cached_interests == interests, "ユーザー興味取得に失敗"
        assert cached_skills == skills, "ユーザースキル取得に失敗"
        print("✓ ユーザー興味・スキルキャッシュ成功")
        
        # 2. 分析結果キャッシュテスト
        print("2. 分析結果キャッシュテスト")
        
        username = "test_user"
        analysis_data = {
            "username": username,
            "analysis": {
                "personality": "外向的",
                "interests": ["プログラミング", "データ分析"],
                "skills": ["Python", "SQL"]
            },
            "confidence": 0.85
        }
        
        # Twitter分析結果設定・取得
        success = strategies.analysis_results.set_twitter_analysis(username, analysis_data)
        assert success, "Twitter分析結果設定に失敗"
        
        cached_analysis = strategies.analysis_results.get_twitter_analysis(username)
        assert cached_analysis['username'] == username, "Twitter分析結果取得に失敗"
        assert 'cached_at' in cached_analysis, "キャッシュ時刻が記録されていない"
        print("✓ Twitter分析結果キャッシュ成功")
        
        # 3. マッチング結果キャッシュテスト
        print("3. マッチング結果キャッシュテスト")
        
        matches = [
            {"user_id": 456, "name": "佐藤花子", "similarity": 0.92},
            {"user_id": 789, "name": "鈴木一郎", "similarity": 0.87}
        ]
        
        # マッチング結果設定・取得
        success = strategies.matching_results.set_user_matches(user_id, matches, 5)
        assert success, "マッチング結果設定に失敗"
        
        cached_matches = strategies.matching_results.get_user_matches(user_id, 5)
        assert cached_matches['matches'] == matches, "マッチング結果取得に失敗"
        assert cached_matches['user_id'] == user_id, "ユーザーID不一致"
        print("✓ マッチング結果キャッシュ成功")
        
        # 類似度スコア設定・取得
        similarity_scores = {
            "interests": 0.85,
            "skills": 0.90,
            "personality": 0.75,
            "overall": 0.83
        }
        
        success = strategies.matching_results.set_similarity_scores(user_id, 456, similarity_scores)
        assert success, "類似度スコア設定に失敗"
        
        cached_scores = strategies.matching_results.get_similarity_scores(user_id, 456)
        assert cached_scores['scores'] == similarity_scores, "類似度スコア取得に失敗"
        print("✓ 類似度スコアキャッシュ成功")
        
        # 4. APIレスポンスキャッシュテスト
        print("4. APIレスポンスキャッシュテスト")
        
        # 学習リソース設定・取得
        resources = [
            {"title": "Python入門", "url": "https://example.com/python", "rating": 4.5},
            {"title": "データ分析基礎", "url": "https://example.com/data", "rating": 4.2}
        ]
        
        success = strategies.api_responses.set_learning_resources("programming", resources, 10)
        assert success, "学習リソース設定に失敗"
        
        cached_resources = strategies.api_responses.get_learning_resources("programming", 10)
        assert cached_resources['resources'] == resources, "学習リソース取得に失敗"
        assert cached_resources['category'] == "programming", "カテゴリ不一致"
        print("✓ 学習リソースキャッシュ成功")
        
        # 5. セッションキャッシュテスト
        print("5. セッションキャッシュテスト")
        
        session_id = "session_123456"
        session_data = {
            "user_id": user_id,
            "login_time": datetime.now(timezone.utc).isoformat(),
            "preferences": {"theme": "dark", "language": "ja"}
        }
        
        # セッションデータ設定・取得
        success = strategies.session_data.set_session_data(session_id, session_data)
        assert success, "セッションデータ設定に失敗"
        
        cached_session = strategies.session_data.get_session_data(session_id)
        assert cached_session['user_id'] == user_id, "セッションデータ取得に失敗"
        assert 'last_accessed' in cached_session, "最終アクセス時刻が記録されていない"
        print("✓ セッションデータキャッシュ成功")
        
        # 6. キャッシュ無効化テスト
        print("6. キャッシュ無効化テスト")
        
        # ユーザー関連キャッシュを無効化
        results = strategies.invalidate_all_user_cache(user_id)
        
        # 無効化後の確認
        assert strategies.user_data.get_user_profile(user_id) is None, "プロファイルキャッシュが無効化されていない"
        assert strategies.user_data.get_user_interests(user_id) is None, "興味キャッシュが無効化されていない"
        
        print(f"✓ キャッシュ無効化成功: {results}")
        
        # 7. キャッシュ概要テスト
        print("7. キャッシュ概要テスト")
        
        overview = strategies.get_cache_overview()
        assert 'cache_stats' in overview, "キャッシュ統計が含まれていない"
        assert 'health_status' in overview, "ヘルス状況が含まれていない"
        assert 'strategies' in overview, "戦略情報が含まれていない"
        
        print("✓ キャッシュ概要取得成功:")
        print(f"  - Health: {overview['health_status']['status']}")
        print(f"  - Strategies: {len(overview['strategies'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ CacheStrategiesテストエラー: {e}")
        return False
    
    finally:
        # クリーンアップ
        monitoring.stop_background_tasks()


def test_cache_decorator():
    """キャッシュデコレータのテスト"""
    print("\n=== キャッシュデコレータテスト ===")
    
    # MonitoringManagerの初期化
    db = DatabaseManager()
    monitoring = MonitoringManager(db)
    
    # CacheManagerの初期化
    cache = CacheManager(monitoring_manager=monitoring)
    
    try:
        # テスト用の関数を定義
        call_count = 0
        
        @cache.cached(ttl=60, strategy='api_responses')
        def expensive_calculation(x, y):
            nonlocal call_count
            call_count += 1
            time.sleep(0.1)  # 重い処理をシミュレート
            return x * y + call_count
        
        # 1回目の呼び出し
        result1 = expensive_calculation(5, 10)
        assert call_count == 1, "1回目の呼び出しでcall_countが1でない"
        
        # 2回目の呼び出し（同じ引数）
        result2 = expensive_calculation(5, 10)
        assert call_count == 1, "キャッシュが効いていない（call_countが増加）"
        assert result1 == result2, "キャッシュされた結果が一致しない"
        
        # 3回目の呼び出し（異なる引数）
        result3 = expensive_calculation(3, 7)
        assert call_count == 2, "異なる引数での呼び出しでcall_countが増加していない"
        assert result3 != result1, "異なる引数での結果が同じ"
        
        print("✓ キャッシュデコレータ機能成功")
        print(f"  - 関数呼び出し回数: {call_count}")
        print(f"  - 結果1: {result1}, 結果2: {result2}, 結果3: {result3}")
        
        return True
        
    except Exception as e:
        print(f"❌ キャッシュデコレータテストエラー: {e}")
        return False
    
    finally:
        # クリーンアップ
        monitoring.stop_background_tasks()


def test_cache_performance():
    """キャッシュパフォーマンステスト"""
    print("\n=== キャッシュパフォーマンステスト ===")
    
    # MonitoringManagerの初期化
    db = DatabaseManager()
    monitoring = MonitoringManager(db)
    
    # CacheManagerの初期化
    cache = CacheManager(monitoring_manager=monitoring)
    
    try:
        # 大量データのテスト
        print("1. 大量データ書き込みテスト")
        
        start_time = time.time()
        test_data = {"data": "x" * 1000}  # 1KB程度のデータ
        
        for i in range(100):
            cache.set(f"perf:test:{i}", test_data)
        
        write_time = time.time() - start_time
        print(f"✓ 100件書き込み完了: {write_time:.3f}秒")
        
        # 大量データの読み込み
        print("2. 大量データ読み込みテスト")
        
        start_time = time.time()
        hit_count = 0
        
        for i in range(100):
            result = cache.get(f"perf:test:{i}")
            if result is not None:
                hit_count += 1
        
        read_time = time.time() - start_time
        print(f"✓ 100件読み込み完了: {read_time:.3f}秒 (ヒット率: {hit_count}%)")
        
        # 統計情報の確認
        stats = cache.get_stats()
        print(f"✓ 最終統計:")
        print(f"  - 総ヒット数: {stats['hits']}")
        print(f"  - 総ミス数: {stats['misses']}")
        print(f"  - ヒット率: {stats['hit_rate']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ キャッシュパフォーマンステストエラー: {e}")
        return False
    
    finally:
        # クリーンアップ
        monitoring.stop_background_tasks()


def main():
    """メインテスト実行"""
    print("キャッシュシステム統合テスト開始")
    print("=" * 50)
    
    results = []
    
    # 各テストの実行
    results.append(("CacheManager基本機能", test_cache_manager()))
    results.append(("CacheStrategies機能", test_cache_strategies()))
    results.append(("キャッシュデコレータ", test_cache_decorator()))
    results.append(("キャッシュパフォーマンス", test_cache_performance()))
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("テスト結果サマリー")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n総合結果: {passed}/{total} テスト通過")
    
    if passed == total:
        print("🎉 全てのテストが成功しました！")
        return True
    else:
        print("⚠️  一部のテストが失敗しました。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)