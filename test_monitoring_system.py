#!/usr/bin/env python3
"""
監視・運用システムのテスト
MonitoringManagerとMetricsCollectorの統合テスト
"""
import os
import sys
import time
import json
import threading
from datetime import datetime, timezone

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database_manager import DatabaseManager
from monitoring.monitoring_manager import MonitoringManager, AlertSeverity, MetricType
from monitoring.metrics_collector import MetricsCollector


def test_monitoring_manager():
    """MonitoringManagerの基本機能テスト"""
    print("=== MonitoringManager基本機能テスト ===")
    
    # データベース接続
    db = DatabaseManager()
    
    # MonitoringManagerの初期化
    monitoring = MonitoringManager(db)
    
    try:
        # 1. メトリクス記録テスト
        print("1. メトリクス記録テスト")
        monitoring.record_gauge("test.cpu_usage", 75.5, {"host": "test-server"}, "percent")
        monitoring.record_counter("test.requests", 100, {"endpoint": "/api/test"})
        monitoring.record_timer("test.response_time", 250.0, {"method": "GET"})
        monitoring.record_histogram("test.memory_usage", 1024.0, {"process": "python"})
        print("✓ メトリクス記録完了")
        
        # 2. パフォーマンス追跡テスト
        print("2. パフォーマンス追跡テスト")
        monitoring.track_performance("database_query", 150.0, True, {"query": "SELECT * FROM users"})
        monitoring.track_performance("api_call", 300.0, True, {"endpoint": "/api/users"})
        monitoring.track_performance("cache_lookup", 5.0, True, {"key": "user:123"})
        print("✓ パフォーマンス追跡完了")
        
        # 3. アラート作成テスト
        print("3. アラート作成テスト")
        alert_id1 = monitoring.create_alert(
            AlertSeverity.MEDIUM,
            "High CPU Usage",
            "CPU usage is above 80%",
            "system_monitor",
            {"cpu_percent": 85.0}
        )
        
        alert_id2 = monitoring.create_alert(
            AlertSeverity.HIGH,
            "Database Connection Error",
            "Failed to connect to database",
            "database_monitor",
            {"error": "Connection timeout"}
        )
        print(f"✓ アラート作成完了: {alert_id1}, {alert_id2}")
        
        # 4. メトリクス取得テスト
        print("4. メトリクス取得テスト")
        metrics = monitoring.get_metrics(hours=1)
        print(f"✓ 取得したメトリクス数: {len(metrics)}")
        
        if metrics:
            print("最新メトリクス例:")
            for metric in metrics[-3:]:
                print(f"  - {metric['name']}: {metric['value']} {metric['unit']} ({metric['type']})")
        
        # 5. アラート取得テスト
        print("5. アラート取得テスト")
        alerts = monitoring.get_alerts(hours=1)
        print(f"✓ 取得したアラート数: {len(alerts)}")
        
        if alerts:
            print("アクティブアラート:")
            for alert in alerts:
                status = "ACTIVE" if not alert['resolved'] else "RESOLVED"
                print(f"  - [{alert['severity'].upper()}] {alert['title']} ({status})")
        
        # 6. パフォーマンス統計テスト
        print("6. パフォーマンス統計テスト")
        perf_stats = monitoring.get_performance_stats(hours=1)
        print(f"✓ パフォーマンス統計取得完了: {len(perf_stats)} operations")
        
        for operation, stats in perf_stats.items():
            print(f"  - {operation}: {stats['total_requests']} requests, "
                  f"avg {stats['avg_duration_ms']:.1f}ms, "
                  f"error rate {stats['error_rate']:.1f}%")
        
        # 7. システム概要テスト
        print("7. システム概要テスト")
        overview = monitoring.get_system_overview()
        print("✓ システム概要:")
        print(f"  - 稼働時間: {overview['uptime_human']}")
        print(f"  - 総メトリクス数: {overview['total_metrics']}")
        print(f"  - アクティブアラート数: {overview['active_alerts']}")
        print(f"  - システム健全性: {overview['system_health']}")
        
        # 8. アラート解決テスト
        print("8. アラート解決テスト")
        monitoring.resolve_alert(alert_id1, "CPU usage returned to normal")
        print(f"✓ アラート解決完了: {alert_id1}")
        
        return True
        
    except Exception as e:
        print(f"❌ MonitoringManagerテストエラー: {e}")
        return False
    
    finally:
        # クリーンアップ
        monitoring.stop_background_tasks()


def test_metrics_collector():
    """MetricsCollectorの機能テスト"""
    print("\n=== MetricsCollector機能テスト ===")
    
    # データベース接続
    db = DatabaseManager()
    
    # MonitoringManagerの初期化
    monitoring = MonitoringManager(db)
    
    # MetricsCollectorの初期化
    collector = MetricsCollector(monitoring, db)
    
    try:
        # 1. カスタムコレクター登録テスト
        print("1. カスタムコレクター登録テスト")
        
        def custom_test_collector():
            """テスト用カスタムコレクター"""
            monitoring.record_gauge("custom.test_metric", 42.0, {"source": "test"})
            monitoring.record_counter("custom.test_counter", 1, {"source": "test"})
        
        collector.register_collector("test_collector", custom_test_collector, 5)
        print("✓ カスタムコレクター登録完了")
        
        # 2. メトリクス収集開始テスト
        print("2. メトリクス収集開始テスト")
        collector.start_collection()
        print("✓ メトリクス収集開始")
        
        # 3. 収集状況確認
        print("3. 収集状況確認")
        time.sleep(10)  # 10秒間収集を実行
        
        summary = collector.get_metrics_summary()
        print("✓ 収集サマリー:")
        print(f"  - 実行中コレクター数: {summary['collectors_running']}")
        print(f"  - 総コレクター数: {summary['total_collectors']}")
        print(f"  - 登録済みコレクター: {summary['registered_collectors']}")
        
        # 4. 収集されたメトリクスの確認
        print("4. 収集されたメトリクスの確認")
        metrics = monitoring.get_metrics(hours=1)
        
        # システムメトリクスの確認
        system_metrics = [m for m in metrics if m['name'].startswith('system.')]
        print(f"✓ システムメトリクス数: {len(system_metrics)}")
        
        # アプリケーションメトリクスの確認
        app_metrics = [m for m in metrics if m['name'].startswith('python.') or m['name'].startswith('database.')]
        print(f"✓ アプリケーションメトリクス数: {len(app_metrics)}")
        
        # カスタムメトリクスの確認
        custom_metrics = [m for m in metrics if m['name'].startswith('custom.')]
        print(f"✓ カスタムメトリクス数: {len(custom_metrics)}")
        
        # 5. 最新メトリクスの表示
        print("5. 最新メトリクス例:")
        recent_metrics = sorted(metrics, key=lambda x: x['timestamp'], reverse=True)[:10]
        for metric in recent_metrics:
            print(f"  - {metric['name']}: {metric['value']} {metric['unit']} "
                  f"({metric['timestamp'][:19]})")
        
        return True
        
    except Exception as e:
        print(f"❌ MetricsCollectorテストエラー: {e}")
        return False
    
    finally:
        # クリーンアップ
        collector.stop_collection()
        monitoring.stop_background_tasks()


def test_integration():
    """統合テスト"""
    print("\n=== 統合テスト ===")
    
    # データベース接続
    db = DatabaseManager()
    
    # MonitoringManagerの初期化
    monitoring = MonitoringManager(db)
    
    # MetricsCollectorの初期化
    collector = MetricsCollector(monitoring, db)
    
    try:
        # 1. 統合システム開始
        print("1. 統合システム開始")
        collector.start_collection()
        print("✓ 統合システム開始完了")
        
        # 2. 負荷シミュレーション
        print("2. 負荷シミュレーション")
        
        def simulate_load():
            """負荷シミュレーション"""
            for i in range(50):
                # API呼び出しシミュレーション
                response_time = 100 + (i % 10) * 20  # 100-280ms
                success = i % 10 != 9  # 10%のエラー率
                
                monitoring.track_performance(
                    f"api_endpoint_{i % 3}",
                    response_time,
                    success,
                    {"request_id": f"req_{i}"}
                )
                
                # データベースクエリシミュレーション
                query_time = 50 + (i % 5) * 10  # 50-90ms
                monitoring.track_performance(
                    "database_query",
                    query_time,
                    True,
                    {"query_type": "SELECT"}
                )
                
                time.sleep(0.1)  # 100ms間隔
        
        # 負荷シミュレーションを別スレッドで実行
        load_thread = threading.Thread(target=simulate_load, daemon=True)
        load_thread.start()
        
        # 3. リアルタイム監視
        print("3. リアルタイム監視（15秒間）")
        for i in range(15):
            time.sleep(1)
            
            # システム概要の取得
            overview = monitoring.get_system_overview()
            
            # アクティブアラートの確認
            active_alerts = monitoring.get_alerts(active_only=True, hours=1)
            
            print(f"  [{i+1:2d}s] メトリクス: {overview['total_metrics']}, "
                  f"アクティブアラート: {len(active_alerts)}, "
                  f"健全性: {overview['system_health']}")
        
        # 4. 最終統計
        print("4. 最終統計")
        
        # パフォーマンス統計
        perf_stats = monitoring.get_performance_stats(hours=1)
        print(f"✓ パフォーマンス統計: {len(perf_stats)} operations")
        
        for operation, stats in perf_stats.items():
            if stats['total_requests'] > 0:
                print(f"  - {operation}: {stats['total_requests']} requests, "
                      f"avg {stats['avg_duration_ms']:.1f}ms, "
                      f"error rate {stats['error_rate']:.1f}%")
        
        # アラート統計
        all_alerts = monitoring.get_alerts(hours=1)
        alert_summary = {}
        for alert in all_alerts:
            severity = alert['severity']
            alert_summary[severity] = alert_summary.get(severity, 0) + 1
        
        print(f"✓ アラート統計: {alert_summary}")
        
        # メトリクス統計
        all_metrics = monitoring.get_metrics(hours=1)
        metric_types = {}
        for metric in all_metrics:
            metric_type = metric['type']
            metric_types[metric_type] = metric_types.get(metric_type, 0) + 1
        
        print(f"✓ メトリクス統計: {metric_types}")
        
        return True
        
    except Exception as e:
        print(f"❌ 統合テストエラー: {e}")
        return False
    
    finally:
        # クリーンアップ
        collector.stop_collection()
        monitoring.stop_background_tasks()


def main():
    """メインテスト実行"""
    print("監視・運用システム統合テスト開始")
    print("=" * 50)
    
    results = []
    
    # 各テストの実行
    results.append(("MonitoringManager基本機能", test_monitoring_manager()))
    results.append(("MetricsCollector機能", test_metrics_collector()))
    results.append(("統合テスト", test_integration()))
    
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