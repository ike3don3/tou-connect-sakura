#!/usr/bin/env python3
"""
監視・運用システム統合テスト
AlertManagerとMetricsVisualizerの統合テスト
"""
import os
import sys
import time
import json
from datetime import datetime, timezone

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database_manager import DatabaseManager
from monitoring.monitoring_manager import MonitoringManager, AlertSeverity, MetricType
from monitoring.metrics_collector import MetricsCollector
from monitoring.alert_manager import AlertManager, ThresholdRule
from monitoring.metrics_visualizer import MetricsVisualizer


def test_alert_manager():
    """AlertManagerの機能テスト"""
    print("=== AlertManager機能テスト ===")
    
    # データベース接続
    db = DatabaseManager()
    
    # MonitoringManagerの初期化
    monitoring = MonitoringManager(db)
    
    # AlertManagerの初期化
    alert_manager = AlertManager(monitoring, db)
    
    try:
        # 1. デフォルトルールの確認
        print("1. デフォルトルールの確認")
        rules = alert_manager.get_alert_rules()
        print(f"✓ デフォルトルール数: {len(rules['threshold_rules'])}")
        
        for rule_id, rule in list(rules['threshold_rules'].items())[:3]:
            print(f"  - {rule['metric_name']} {rule['operator']} {rule['threshold_value']}")
        
        # 2. カスタムルールの追加
        print("2. カスタムルールの追加")
        custom_rule = ThresholdRule(
            metric_name="test.custom_metric",
            operator=">=",
            threshold_value=100.0,
            duration_minutes=1,
            severity=AlertSeverity.HIGH,
            description="テスト用カスタムルール"
        )
        
        rule_id = alert_manager.add_threshold_rule(custom_rule)
        print(f"✓ カスタムルール追加: {rule_id}")
        
        # 3. 通知チャネルの確認
        print("3. 通知チャネルの確認")
        channels = alert_manager.get_notification_channels()
        print(f"✓ 設定済み通知チャネル数: {len(channels)}")
        
        for name, config in channels.items():
            print(f"  - {name}: {config['channel']} (enabled: {config['enabled']})")
        
        # 4. 閾値ルールのテスト
        print("4. 閾値ルールのテスト")
        
        # 閾値を超えるメトリクスを送信
        for i in range(5):
            monitoring.record_gauge("test.custom_metric", 150.0 + i * 10)
            time.sleep(0.2)
        
        time.sleep(2)  # アラート処理を待機
        
        # アラートの確認
        alerts = monitoring.get_alerts(hours=1)
        custom_alerts = [a for a in alerts if 'test.custom_metric' in a.get('message', '')]
        print(f"✓ 生成されたカスタムアラート数: {len(custom_alerts)}")
        
        # 5. アラート統計の確認
        print("5. アラート統計の確認")
        stats = alert_manager.get_alert_statistics()
        print(f"✓ 総アラート数: {stats['total_alerts']}")
        print(f"✓ 通知送信数: {stats['notifications_sent']}")
        print(f"✓ ルール統計: {stats['rules_stats']}")
        
        # 6. ルールの削除
        print("6. ルールの削除")
        success = alert_manager.remove_threshold_rule(rule_id)
        print(f"✓ ルール削除成功: {success}")
        
        return True
        
    except Exception as e:
        print(f"❌ AlertManagerテストエラー: {e}")
        return False
    
    finally:
        # クリーンアップ
        monitoring.stop_background_tasks()


def test_metrics_visualizer():
    """MetricsVisualizerの機能テスト"""
    print("\n=== MetricsVisualizer機能テスト ===")
    
    # データベース接続
    db = DatabaseManager()
    
    # MonitoringManagerの初期化
    monitoring = MonitoringManager(db)
    
    # MetricsVisualizerの初期化
    visualizer = MetricsVisualizer(monitoring)
    
    try:
        # テストデータの生成
        print("1. テストデータの生成")
        
        # 複数のメトリクスを生成
        for i in range(50):
            timestamp_offset = i * 60  # 1分間隔
            
            # CPU使用率（周期的な変動）
            cpu_value = 50 + 30 * (i % 10) / 10
            monitoring.record_gauge("system.cpu.usage_percent", cpu_value)
            
            # メモリ使用率（徐々に増加）
            memory_value = 40 + i * 0.5
            monitoring.record_gauge("system.memory.usage_percent", memory_value)
            
            # レスポンス時間（ランダムな変動）
            response_time = 200 + (i % 7) * 50
            monitoring.record_timer("http.request.duration", response_time)
            
            time.sleep(0.05)  # 短い間隔で生成
        
        print("✓ テストデータ生成完了")
        
        # 2. 時系列データの取得
        print("2. 時系列データの取得")
        
        time_series = visualizer.get_time_series_data([
            'system.cpu.usage_percent',
            'system.memory.usage_percent',
            'http.request.duration'
        ], hours=1, interval='1m')
        
        print(f"✓ 時系列データ: {len(time_series['series'])} シリーズ")
        print(f"✓ タイムスタンプ数: {len(time_series['timestamps'])}")
        
        for series in time_series['series']:
            non_null_count = len([v for v in series['data'] if v is not None])
            print(f"  - {series['name']}: {non_null_count} データポイント")
        
        # 3. ダッシュボードデータの取得
        print("3. ダッシュボードデータの取得")
        
        dashboard_data = visualizer.get_dashboard_data(hours=1)
        
        if 'error' not in dashboard_data:
            print("✓ ダッシュボードデータ取得成功")
            print(f"  - システムメトリクス: {len(dashboard_data['system_metrics']['series'])} シリーズ")
            print(f"  - アプリケーションメトリクス: {len(dashboard_data['application_metrics']['series'])} シリーズ")
            print(f"  - トップメトリクス: {len(dashboard_data['top_metrics'])} 項目")
        else:
            print(f"⚠️ ダッシュボードデータエラー: {dashboard_data['error']}")
        
        # 4. ヒストグラムの生成
        print("4. ヒストグラムの生成")
        
        histogram = visualizer.get_metric_histogram('http.request.duration', hours=1, bins=10)
        
        if histogram['bins']:
            print(f"✓ ヒストグラム生成成功")
            print(f"  - ビン数: {len(histogram['bins'])}")
            print(f"  - サンプル数: {histogram['metadata']['total_samples']}")
            print(f"  - 平均値: {histogram['metadata']['mean']:.2f}")
            print(f"  - P95: {histogram['metadata']['p95']:.2f}")
        else:
            print("⚠️ ヒストグラムデータなし")
        
        # 5. 相関行列の計算
        print("5. 相関行列の計算")
        
        correlation = visualizer.get_correlation_matrix([
            'system.cpu.usage_percent',
            'system.memory.usage_percent'
        ], hours=1)
        
        if correlation['matrix']:
            print(f"✓ 相関行列計算成功")
            print(f"  - メトリクス数: {len(correlation['labels'])}")
            print(f"  - サンプルサイズ: {correlation['metadata']['sample_size']}")
            
            # 相関係数を表示
            for i, label1 in enumerate(correlation['labels']):
                for j, label2 in enumerate(correlation['labels']):
                    if i < j:  # 上三角のみ表示
                        corr_value = correlation['matrix'][i][j]
                        print(f"  - {label1} vs {label2}: {corr_value:.3f}")
        else:
            print("⚠️ 相関行列データなし")
        
        # 6. 異常検知
        print("6. 異常検知")
        
        # 異常値を追加
        monitoring.record_gauge("system.cpu.usage_percent", 95.0)  # 異常に高い値
        monitoring.record_gauge("system.cpu.usage_percent", 5.0)   # 異常に低い値
        
        anomalies = visualizer.get_anomaly_detection('system.cpu.usage_percent', hours=1, sensitivity=1.5)
        
        if anomalies['anomalies']:
            print(f"✓ 異常検知実行成功")
            print(f"  - 検出された異常数: {len(anomalies['anomalies'])}")
            print(f"  - 異常率: {anomalies['metadata']['anomaly_rate']:.2f}%")
            
            for anomaly in anomalies['anomalies'][:3]:  # 最初の3件を表示
                print(f"  - 異常値: {anomaly['value']:.2f} (期待値: {anomaly['expected']:.2f}, Z-score: {anomaly['z_score']:.2f})")
        else:
            print("⚠️ 異常検知データなし")
        
        # 7. データエクスポート
        print("7. データエクスポート")
        
        # JSON形式でエクスポート
        json_data = visualizer.export_metrics_data(['system.cpu.usage_percent'], hours=1, format='json')
        json_obj = json.loads(json_data)
        print(f"✓ JSONエクスポート成功: {len(json_obj['series'])} シリーズ")
        
        # CSV形式でエクスポート
        csv_data = visualizer.export_metrics_data(['system.cpu.usage_percent'], hours=1, format='csv')
        csv_lines = csv_data.split('\n')
        print(f"✓ CSVエクスポート成功: {len(csv_lines)} 行")
        
        return True
        
    except Exception as e:
        print(f"❌ MetricsVisualizerテストエラー: {e}")
        return False
    
    finally:
        # クリーンアップ
        monitoring.stop_background_tasks()


def test_integration():
    """統合テスト"""
    print("\n=== 統合テスト ===")
    
    # データベース接続
    db = DatabaseManager()
    
    # 全コンポーネントの初期化
    monitoring = MonitoringManager(db)
    metrics_collector = MetricsCollector(monitoring, db)
    alert_manager = AlertManager(monitoring, db)
    visualizer = MetricsVisualizer(monitoring)
    
    try:
        # 1. システム全体の開始
        print("1. システム全体の開始")
        metrics_collector.start_collection()
        print("✓ 全コンポーネント開始完了")
        
        # 2. 負荷シミュレーション
        print("2. 負荷シミュレーション")
        
        # 高負荷状態をシミュレート
        for i in range(20):
            # CPU使用率が徐々に上昇
            cpu_usage = 60 + i * 2
            monitoring.record_gauge("system.cpu.usage_percent", cpu_usage)
            
            # メモリ使用率も上昇
            memory_usage = 70 + i * 1.5
            monitoring.record_gauge("system.memory.usage_percent", memory_usage)
            
            # レスポンス時間が悪化
            response_time = 1000 + i * 100
            monitoring.record_timer("http.request.duration", response_time)
            
            time.sleep(0.1)
        
        print("✓ 負荷シミュレーション完了")
        
        # 3. アラートの確認
        print("3. アラートの確認")
        time.sleep(3)  # アラート処理を待機
        
        alerts = monitoring.get_alerts(hours=1)
        threshold_alerts = [a for a in alerts if a['source'] == 'threshold_monitor']
        
        print(f"✓ 生成されたアラート数: {len(alerts)}")
        print(f"✓ 閾値アラート数: {len(threshold_alerts)}")
        
        # 4. 可視化データの生成
        print("4. 可視化データの生成")
        
        dashboard_data = visualizer.get_dashboard_data(hours=1)
        
        if 'error' not in dashboard_data:
            print("✓ ダッシュボードデータ生成成功")
            
            # システムメトリクスの確認
            system_series = dashboard_data['system_metrics']['series']
            for series in system_series:
                if series['name'] == 'system.cpu.usage_percent':
                    latest_values = [v for v in series['data'][-5:] if v is not None]
                    if latest_values:
                        avg_cpu = sum(latest_values) / len(latest_values)
                        print(f"  - 最新CPU使用率平均: {avg_cpu:.1f}%")
        
        # 5. アラート統計の確認
        print("5. アラート統計の確認")
        
        alert_stats = alert_manager.get_alert_statistics()
        print(f"✓ 総アラート数: {alert_stats['total_alerts']}")
        print(f"✓ アクティブルール数: {alert_stats['rules_stats']['active_rules']}")
        
        # 6. システム概要の確認
        print("6. システム概要の確認")
        
        overview = monitoring.get_system_overview()
        print(f"✓ システム健全性: {overview['system_health']}")
        print(f"✓ 総メトリクス数: {overview['total_metrics']}")
        print(f"✓ アクティブアラート数: {overview['active_alerts']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 統合テストエラー: {e}")
        return False
    
    finally:
        # クリーンアップ
        metrics_collector.stop_collection()
        monitoring.stop_background_tasks()


def main():
    """メインテスト実行"""
    print("監視・運用システム統合テスト開始")
    print("=" * 50)
    
    results = []
    
    # 各テストの実行
    results.append(("AlertManager機能", test_alert_manager()))
    results.append(("MetricsVisualizer機能", test_metrics_visualizer()))
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