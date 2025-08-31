"""
MetricsVisualizer - メトリクス可視化システム
時系列データの集約、グラフ生成、ダッシュボード用データ提供
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import statistics

from monitoring.monitoring_manager import MonitoringManager


class MetricsVisualizer:
    """メトリクス可視化システム"""
    
    def __init__(self, monitoring_manager: MonitoringManager):
        self.monitoring = monitoring_manager
        self.logger = logging.getLogger(__name__)
        
        # 集約設定
        self.aggregation_intervals = {
            '1m': 60,      # 1分
            '5m': 300,     # 5分
            '15m': 900,    # 15分
            '1h': 3600,    # 1時間
            '6h': 21600,   # 6時間
            '1d': 86400    # 1日
        }
        
        # 色パレット
        self.color_palette = [
            '#3B82F6', '#EF4444', '#10B981', '#F59E0B',
            '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16',
            '#F97316', '#6366F1', '#14B8A6', '#F43F5E'
        ]
    
    def get_time_series_data(self, metric_names: List[str], hours: int = 24, 
                           interval: str = '5m') -> Dict[str, Any]:
        """時系列データの取得"""
        try:
            # メトリクスデータを取得
            all_metrics = self.monitoring.get_metrics(hours=hours)
            
            # 指定されたメトリクス名でフィルタ
            filtered_metrics = []
            for metric in all_metrics:
                if any(name in metric['name'] for name in metric_names):
                    filtered_metrics.append(metric)
            
            if not filtered_metrics:
                return {'series': [], 'timestamps': [], 'metadata': {}}
            
            # 時間間隔での集約
            aggregated_data = self._aggregate_metrics(filtered_metrics, interval)
            
            # 時系列データの構築
            series_data = self._build_time_series(aggregated_data, metric_names)
            
            return {
                'series': series_data['series'],
                'timestamps': series_data['timestamps'],
                'metadata': {
                    'interval': interval,
                    'hours': hours,
                    'total_points': len(series_data['timestamps']),
                    'metric_count': len(series_data['series'])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Time series data generation failed: {e}")
            return {'series': [], 'timestamps': [], 'metadata': {'error': str(e)}}
    
    def get_dashboard_data(self, hours: int = 24) -> Dict[str, Any]:
        """ダッシュボード用データの取得"""
        try:
            # 主要メトリクスの時系列データ
            system_metrics = self.get_time_series_data([
                'system.cpu.usage_percent',
                'system.memory.usage_percent',
                'system.disk.usage_percent'
            ], hours, '15m')
            
            application_metrics = self.get_time_series_data([
                'http.request.duration',
                'python.memory.rss_mb',
                'database.health_check.response_time'
            ], hours, '15m')
            
            business_metrics = self.get_time_series_data([
                'business.users.total',
                'business.analyses.total',
                'business.revenue.total_clicks'
            ], hours, '1h')
            
            # 統計サマリー
            stats_summary = self._generate_stats_summary(hours)
            
            # トップメトリクス
            top_metrics = self._get_top_metrics(hours)
            
            return {
                'system_metrics': system_metrics,
                'application_metrics': application_metrics,
                'business_metrics': business_metrics,
                'stats_summary': stats_summary,
                'top_metrics': top_metrics,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Dashboard data generation failed: {e}")
            return {'error': str(e)}
    
    def get_metric_histogram(self, metric_name: str, hours: int = 24, 
                           bins: int = 20) -> Dict[str, Any]:
        """メトリクスヒストグラムの生成"""
        try:
            metrics = self.monitoring.get_metrics(metric_name, hours)
            
            if not metrics:
                return {'bins': [], 'counts': [], 'metadata': {}}
            
            values = [m['value'] for m in metrics]
            
            # ヒストグラムの計算
            min_val = min(values)
            max_val = max(values)
            
            if min_val == max_val:
                return {
                    'bins': [min_val],
                    'counts': [len(values)],
                    'metadata': {
                        'total_samples': len(values),
                        'min_value': min_val,
                        'max_value': max_val,
                        'mean': min_val,
                        'std_dev': 0
                    }
                }
            
            bin_width = (max_val - min_val) / bins
            bin_edges = [min_val + i * bin_width for i in range(bins + 1)]
            bin_counts = [0] * bins
            
            for value in values:
                bin_index = min(int((value - min_val) / bin_width), bins - 1)
                bin_counts[bin_index] += 1
            
            return {
                'bins': bin_edges[:-1],  # 左端の値
                'counts': bin_counts,
                'metadata': {
                    'total_samples': len(values),
                    'min_value': min_val,
                    'max_value': max_val,
                    'mean': statistics.mean(values),
                    'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                    'median': statistics.median(values),
                    'p95': self._percentile(values, 95),
                    'p99': self._percentile(values, 99)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Histogram generation failed: {e}")
            return {'bins': [], 'counts': [], 'metadata': {'error': str(e)}}
    
    def get_correlation_matrix(self, metric_names: List[str], 
                             hours: int = 24) -> Dict[str, Any]:
        """メトリクス相関行列の計算"""
        try:
            # 各メトリクスのデータを取得
            metric_data = {}
            
            for metric_name in metric_names:
                metrics = self.monitoring.get_metrics(metric_name, hours)
                if metrics:
                    # 時刻でソートして値のリストを作成
                    sorted_metrics = sorted(metrics, key=lambda x: x['timestamp'])
                    metric_data[metric_name] = [m['value'] for m in sorted_metrics]
            
            if len(metric_data) < 2:
                return {'matrix': [], 'labels': [], 'metadata': {}}
            
            # データ長を揃える（最短のものに合わせる）
            min_length = min(len(values) for values in metric_data.values())
            for name in metric_data:
                metric_data[name] = metric_data[name][:min_length]
            
            # 相関行列の計算
            labels = list(metric_data.keys())
            matrix = []
            
            for i, name1 in enumerate(labels):
                row = []
                for j, name2 in enumerate(labels):
                    if i == j:
                        correlation = 1.0
                    else:
                        correlation = self._calculate_correlation(
                            metric_data[name1], 
                            metric_data[name2]
                        )
                    row.append(correlation)
                matrix.append(row)
            
            return {
                'matrix': matrix,
                'labels': labels,
                'metadata': {
                    'sample_size': min_length,
                    'metric_count': len(labels)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Correlation matrix calculation failed: {e}")
            return {'matrix': [], 'labels': [], 'metadata': {'error': str(e)}}
    
    def get_anomaly_detection(self, metric_name: str, hours: int = 24, 
                            sensitivity: float = 2.0) -> Dict[str, Any]:
        """異常検知の実行"""
        try:
            metrics = self.monitoring.get_metrics(metric_name, hours)
            
            if len(metrics) < 10:  # 最低10データポイント必要
                return {'anomalies': [], 'threshold': None, 'metadata': {}}
            
            # 時刻でソート
            sorted_metrics = sorted(metrics, key=lambda x: x['timestamp'])
            values = [m['value'] for m in sorted_metrics]
            
            # 移動平均と標準偏差を計算
            window_size = min(20, len(values) // 4)
            anomalies = []
            
            for i in range(window_size, len(values)):
                window = values[i-window_size:i]
                mean = statistics.mean(window)
                std_dev = statistics.stdev(window) if len(window) > 1 else 0
                
                current_value = values[i]
                z_score = abs(current_value - mean) / std_dev if std_dev > 0 else 0
                
                if z_score > sensitivity:
                    anomalies.append({
                        'timestamp': sorted_metrics[i]['timestamp'],
                        'value': current_value,
                        'expected': mean,
                        'z_score': z_score,
                        'deviation': current_value - mean
                    })
            
            # 全体統計
            overall_mean = statistics.mean(values)
            overall_std = statistics.stdev(values) if len(values) > 1 else 0
            threshold = overall_mean + sensitivity * overall_std
            
            return {
                'anomalies': anomalies,
                'threshold': threshold,
                'metadata': {
                    'total_points': len(values),
                    'anomaly_count': len(anomalies),
                    'anomaly_rate': len(anomalies) / len(values) * 100,
                    'sensitivity': sensitivity,
                    'overall_mean': overall_mean,
                    'overall_std': overall_std
                }
            }
            
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {e}")
            return {'anomalies': [], 'threshold': None, 'metadata': {'error': str(e)}}
    
    def _aggregate_metrics(self, metrics: List[Dict[str, Any]], 
                          interval: str) -> Dict[str, List[Dict[str, Any]]]:
        """メトリクスの時間間隔集約"""
        interval_seconds = self.aggregation_intervals.get(interval, 300)
        
        # メトリクス名でグループ化
        grouped_metrics = defaultdict(list)
        for metric in metrics:
            grouped_metrics[metric['name']].append(metric)
        
        aggregated = {}
        
        for metric_name, metric_list in grouped_metrics.items():
            # 時刻でソート
            sorted_metrics = sorted(metric_list, key=lambda x: x['timestamp'])
            
            # 時間間隔でバケット化
            buckets = defaultdict(list)
            
            for metric in sorted_metrics:
                timestamp = datetime.fromisoformat(metric['timestamp'].replace('Z', '+00:00'))
                bucket_key = int(timestamp.timestamp() // interval_seconds) * interval_seconds
                buckets[bucket_key].append(metric['value'])
            
            # 各バケットの統計を計算
            aggregated_points = []
            for bucket_timestamp, values in sorted(buckets.items()):
                if values:
                    aggregated_points.append({
                        'timestamp': datetime.fromtimestamp(bucket_timestamp, timezone.utc).isoformat(),
                        'value': statistics.mean(values),
                        'min': min(values),
                        'max': max(values),
                        'count': len(values),
                        'std_dev': statistics.stdev(values) if len(values) > 1 else 0
                    })
            
            aggregated[metric_name] = aggregated_points
        
        return aggregated
    
    def _build_time_series(self, aggregated_data: Dict[str, List[Dict[str, Any]]], 
                          metric_names: List[str]) -> Dict[str, Any]:
        """時系列データの構築"""
        # 全タイムスタンプを収集
        all_timestamps = set()
        for metric_data in aggregated_data.values():
            for point in metric_data:
                all_timestamps.add(point['timestamp'])
        
        sorted_timestamps = sorted(list(all_timestamps))
        
        # 各メトリクスのシリーズデータを構築
        series = []
        color_index = 0
        
        for metric_name, metric_data in aggregated_data.items():
            # データポイントを辞書に変換（高速検索用）
            data_dict = {point['timestamp']: point for point in metric_data}
            
            # 全タイムスタンプに対応する値を作成
            values = []
            for timestamp in sorted_timestamps:
                if timestamp in data_dict:
                    values.append(data_dict[timestamp]['value'])
                else:
                    values.append(None)  # 欠損値
            
            series.append({
                'name': metric_name,
                'data': values,
                'color': self.color_palette[color_index % len(self.color_palette)],
                'metadata': {
                    'total_points': len([v for v in values if v is not None]),
                    'missing_points': len([v for v in values if v is None])
                }
            })
            
            color_index += 1
        
        return {
            'series': series,
            'timestamps': sorted_timestamps
        }
    
    def _generate_stats_summary(self, hours: int) -> Dict[str, Any]:
        """統計サマリーの生成"""
        try:
            all_metrics = self.monitoring.get_metrics(hours=hours)
            
            if not all_metrics:
                return {}
            
            # メトリクス種別統計
            type_counts = defaultdict(int)
            for metric in all_metrics:
                type_counts[metric['type']] += 1
            
            # 時間別統計
            hourly_counts = defaultdict(int)
            for metric in all_metrics:
                timestamp = datetime.fromisoformat(metric['timestamp'].replace('Z', '+00:00'))
                hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                hourly_counts[hour_key] += 1
            
            # トップメトリクス名
            name_counts = defaultdict(int)
            for metric in all_metrics:
                name_counts[metric['name']] += 1
            
            top_metrics = sorted(name_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'total_metrics': len(all_metrics),
                'type_distribution': dict(type_counts),
                'hourly_distribution': dict(hourly_counts),
                'top_metrics': [{'name': name, 'count': count} for name, count in top_metrics],
                'time_range': f'{hours} hours'
            }
            
        except Exception as e:
            self.logger.error(f"Stats summary generation failed: {e}")
            return {'error': str(e)}
    
    def _get_top_metrics(self, hours: int, limit: int = 20) -> List[Dict[str, Any]]:
        """トップメトリクスの取得"""
        try:
            all_metrics = self.monitoring.get_metrics(hours=hours)
            
            # メトリクス名別に最新値と統計を計算
            metric_stats = defaultdict(list)
            for metric in all_metrics:
                metric_stats[metric['name']].append(metric['value'])
            
            top_metrics = []
            for name, values in metric_stats.items():
                if values:
                    latest_value = values[-1]  # 最新値
                    avg_value = statistics.mean(values)
                    
                    top_metrics.append({
                        'name': name,
                        'latest_value': latest_value,
                        'average_value': avg_value,
                        'sample_count': len(values),
                        'min_value': min(values),
                        'max_value': max(values)
                    })
            
            # サンプル数でソート
            top_metrics.sort(key=lambda x: x['sample_count'], reverse=True)
            
            return top_metrics[:limit]
            
        except Exception as e:
            self.logger.error(f"Top metrics generation failed: {e}")
            return []
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """パーセンタイル計算"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            
            return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """相関係数の計算"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        sum_y2 = sum(yi * yi for yi in y)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def export_metrics_data(self, metric_names: List[str], hours: int = 24, 
                           format: str = 'json') -> str:
        """メトリクスデータのエクスポート"""
        try:
            time_series_data = self.get_time_series_data(metric_names, hours)
            
            if format.lower() == 'json':
                return json.dumps(time_series_data, indent=2, ensure_ascii=False)
            elif format.lower() == 'csv':
                return self._export_to_csv(time_series_data)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            self.logger.error(f"Metrics export failed: {e}")
            return f"Export failed: {e}"
    
    def _export_to_csv(self, time_series_data: Dict[str, Any]) -> str:
        """CSV形式でのエクスポート"""
        if not time_series_data['series']:
            return "No data available"
        
        lines = []
        
        # ヘッダー行
        header = ['timestamp']
        for series in time_series_data['series']:
            header.append(series['name'])
        lines.append(','.join(header))
        
        # データ行
        timestamps = time_series_data['timestamps']
        for i, timestamp in enumerate(timestamps):
            row = [timestamp]
            for series in time_series_data['series']:
                value = series['data'][i] if i < len(series['data']) else None
                row.append(str(value) if value is not None else '')
            lines.append(','.join(row))
        
        return '\n'.join(lines)