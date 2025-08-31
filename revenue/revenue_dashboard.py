"""
RevenueDashboard - 収益分析ダッシュボード
収益レポート、パフォーマンス分析、予測機能
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import statistics

from revenue.affiliate_tracker import AffiliateTracker


@dataclass
class RevenueMetrics:
    """収益メトリクス"""
    total_revenue: float
    total_conversions: int
    conversion_rate: float
    average_order_value: float
    revenue_per_click: float
    growth_rate: float


class RevenueDashboard:
    """収益分析ダッシュボード"""
    
    def __init__(self, affiliate_tracker: AffiliateTracker, 
                 db_manager=None, monitoring_manager=None):
        self.affiliate_tracker = affiliate_tracker
        self.db = db_manager
        self.monitoring = monitoring_manager
        self.logger = logging.getLogger(__name__)
    
    def get_dashboard_overview(self, days: int = 30) -> Dict[str, Any]:
        """ダッシュボード概要の取得"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # 現在期間のデータ
            current_report = self.affiliate_tracker.get_revenue_report(
                start_date=start_date, end_date=end_date
            )
            
            # 前期間のデータ（比較用）
            prev_end_date = start_date
            prev_start_date = prev_end_date - timedelta(days=days)
            prev_report = self.affiliate_tracker.get_revenue_report(
                start_date=prev_start_date, end_date=prev_end_date
            )
            
            # 成長率計算
            growth_rates = self._calculate_growth_rates(current_report, prev_report)
            
            # トップパフォーマー
            top_affiliates = self._get_top_affiliates(days)
            top_resources = current_report.get('top_performing_resources', [])
            
            overview = {
                'period': {
                    'days': days,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': current_report.get('summary', {}),
                'growth_rates': growth_rates,
                'top_affiliates': top_affiliates,
                'top_resources': top_resources[:5],  # トップ5
                'revenue_trends': current_report.get('revenue_by_day', {}),
                'conversion_funnel': self._get_conversion_funnel_data(days),
                'performance_alerts': self._generate_performance_alerts(current_report, prev_report)
            }
            
            return overview
            
        except Exception as e:
            self.logger.error(f"Dashboard overview generation failed: {e}")
            return {'error': str(e)}
    
    def get_affiliate_comparison(self, days: int = 30) -> Dict[str, Any]:
        """アフィリエイト比較分析"""
        try:
            affiliates = list(self.affiliate_tracker.affiliate_partners.keys())
            comparison_data = []
            
            for affiliate_id in affiliates:
                performance = self.affiliate_tracker.get_affiliate_performance(affiliate_id)
                if performance:
                    comparison_data.append(performance)
            
            # ソート（収益順）
            comparison_data.sort(key=lambda x: x.get('metrics', {}).get('total_revenue', 0), reverse=True)
            
            # 統計計算
            revenues = [a.get('metrics', {}).get('total_revenue', 0) for a in comparison_data]
            conversion_rates = [a.get('metrics', {}).get('conversion_rate', 0) for a in comparison_data]
            
            comparison = {
                'affiliates': comparison_data,
                'statistics': {
                    'total_affiliates': len(comparison_data),
                    'average_revenue': statistics.mean(revenues) if revenues else 0,
                    'median_revenue': statistics.median(revenues) if revenues else 0,
                    'average_conversion_rate': statistics.mean(conversion_rates) if conversion_rates else 0,
                    'best_performer': comparison_data[0] if comparison_data else None,
                    'revenue_distribution': self._calculate_revenue_distribution(revenues)
                }
            }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Affiliate comparison failed: {e}")
            return {'error': str(e)}
    
    def get_revenue_forecast(self, days_ahead: int = 30) -> Dict[str, Any]:
        """収益予測"""
        try:
            # 過去90日のデータを使用して予測
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=90)
            
            historical_report = self.affiliate_tracker.get_revenue_report(
                start_date=start_date, end_date=end_date
            )
            
            daily_revenues = historical_report.get('revenue_by_day', {})
            
            if not daily_revenues:
                return {'error': 'Insufficient historical data for forecasting'}
            
            # 簡単な線形予測
            forecast = self._calculate_linear_forecast(daily_revenues, days_ahead)
            
            # 信頼区間の計算
            confidence_intervals = self._calculate_confidence_intervals(daily_revenues, forecast)
            
            forecast_data = {
                'forecast_period': {
                    'start_date': end_date.isoformat(),
                    'end_date': (end_date + timedelta(days=days_ahead)).isoformat(),
                    'days': days_ahead
                },
                'historical_data': daily_revenues,
                'forecast': forecast,
                'confidence_intervals': confidence_intervals,
                'summary': {
                    'predicted_total_revenue': sum(forecast.values()),
                    'average_daily_revenue': sum(forecast.values()) / len(forecast),
                    'growth_trend': self._calculate_growth_trend(daily_revenues)
                }
            }
            
            return forecast_data
            
        except Exception as e:
            self.logger.error(f"Revenue forecast failed: {e}")
            return {'error': str(e)}
    
    def get_conversion_analysis(self, days: int = 30) -> Dict[str, Any]:
        """コンバージョン分析"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # クリックとコンバージョンデータの取得
            click_analytics = self.affiliate_tracker.get_click_analytics(
                start_date=start_date, end_date=end_date
            )
            
            # コンバージョンファネル分析
            funnel_data = click_analytics.get('conversion_funnel', {})
            
            # ソース別コンバージョン率
            source_conversion_rates = self._calculate_source_conversion_rates(days)
            
            # 時間別コンバージョンパターン
            hourly_patterns = self._analyze_hourly_conversion_patterns(days)
            
            analysis = {
                'period': {
                    'days': days,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'funnel_analysis': funnel_data,
                'source_performance': source_conversion_rates,
                'temporal_patterns': {
                    'hourly_conversions': hourly_patterns,
                    'best_conversion_hours': self._get_best_conversion_hours(hourly_patterns),
                    'conversion_velocity': self._calculate_conversion_velocity(days)
                },
                'optimization_recommendations': self._generate_optimization_recommendations(
                    source_conversion_rates, hourly_patterns
                )
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Conversion analysis failed: {e}")
            return {'error': str(e)}
    
    def get_revenue_attribution(self, days: int = 30) -> Dict[str, Any]:
        """収益アトリビューション分析"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # コンバージョンデータの取得
            conversions = self.affiliate_tracker._get_conversions_from_db(
                start_date=start_date, end_date=end_date
            )
            
            attribution_data = {
                'first_click_attribution': {},
                'last_click_attribution': {},
                'linear_attribution': {},
                'time_decay_attribution': {}
            }
            
            # 各コンバージョンについてアトリビューション分析
            for conversion in conversions:
                click_id = conversion.get('click_id')
                revenue = self.affiliate_tracker._calculate_revenue_from_conversion(conversion)
                
                if click_id:
                    click_info = self.affiliate_tracker._get_click_from_db(click_id)
                    if click_info:
                        source = click_info.get('source', 'unknown')
                        
                        # 簡単な実装: ラストクリックアトリビューション
                        attribution_data['last_click_attribution'][source] = \
                            attribution_data['last_click_attribution'].get(source, 0) + revenue
            
            # アトリビューション比較
            attribution_comparison = self._compare_attribution_models(attribution_data)
            
            return {
                'period': {
                    'days': days,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'attribution_models': attribution_data,
                'model_comparison': attribution_comparison,
                'insights': self._generate_attribution_insights(attribution_data)
            }
            
        except Exception as e:
            self.logger.error(f"Revenue attribution analysis failed: {e}")
            return {'error': str(e)}
    
    def _calculate_growth_rates(self, current_report: Dict[str, Any], 
                               prev_report: Dict[str, Any]) -> Dict[str, float]:
        """成長率計算"""
        try:
            current_summary = current_report.get('summary', {})
            prev_summary = prev_report.get('summary', {})
            
            growth_rates = {}
            
            metrics = ['total_revenue', 'total_conversions', 'conversion_rate', 'average_order_value']
            
            for metric in metrics:
                current_value = current_summary.get(metric, 0)
                prev_value = prev_summary.get(metric, 0)
                
                if prev_value > 0:
                    growth_rate = ((current_value - prev_value) / prev_value) * 100
                else:
                    growth_rate = 100 if current_value > 0 else 0
                
                growth_rates[metric] = growth_rate
            
            return growth_rates
            
        except Exception as e:
            self.logger.error(f"Growth rate calculation failed: {e}")
            return {}
    
    def _get_top_affiliates(self, days: int) -> List[Dict[str, Any]]:
        """トップアフィリエイトの取得"""
        try:
            affiliates = list(self.affiliate_tracker.affiliate_partners.keys())
            affiliate_performance = []
            
            for affiliate_id in affiliates:
                performance = self.affiliate_tracker.get_affiliate_performance(affiliate_id)
                if performance and performance.get('metrics', {}).get('total_revenue', 0) > 0:
                    affiliate_performance.append(performance)
            
            # 収益順でソート
            affiliate_performance.sort(
                key=lambda x: x.get('metrics', {}).get('total_revenue', 0), 
                reverse=True
            )
            
            return affiliate_performance[:5]  # トップ5
            
        except Exception as e:
            self.logger.error(f"Top affiliates retrieval failed: {e}")
            return []
    
    def _get_conversion_funnel_data(self, days: int) -> Dict[str, Any]:
        """コンバージョンファネルデータの取得"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            click_analytics = self.affiliate_tracker.get_click_analytics(
                start_date=start_date, end_date=end_date
            )
            
            return click_analytics.get('conversion_funnel', {})
            
        except Exception as e:
            self.logger.error(f"Conversion funnel data retrieval failed: {e}")
            return {}
    
    def _generate_performance_alerts(self, current_report: Dict[str, Any], 
                                   prev_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """パフォーマンスアラートの生成"""
        try:
            alerts = []
            
            current_summary = current_report.get('summary', {})
            prev_summary = prev_report.get('summary', {})
            
            # 収益減少アラート
            current_revenue = current_summary.get('total_revenue', 0)
            prev_revenue = prev_summary.get('total_revenue', 0)
            
            if prev_revenue > 0 and current_revenue < prev_revenue * 0.8:  # 20%以上減少
                alerts.append({
                    'type': 'revenue_decline',
                    'severity': 'high',
                    'message': f'収益が前期比{((prev_revenue - current_revenue) / prev_revenue * 100):.1f}%減少しています',
                    'current_value': current_revenue,
                    'previous_value': prev_revenue
                })
            
            # コンバージョン率低下アラート
            current_conv_rate = current_summary.get('conversion_rate', 0)
            prev_conv_rate = prev_summary.get('conversion_rate', 0)
            
            if prev_conv_rate > 0 and current_conv_rate < prev_conv_rate * 0.7:  # 30%以上低下
                alerts.append({
                    'type': 'conversion_rate_decline',
                    'severity': 'medium',
                    'message': f'コンバージョン率が前期比{((prev_conv_rate - current_conv_rate) / prev_conv_rate * 100):.1f}%低下しています',
                    'current_value': current_conv_rate,
                    'previous_value': prev_conv_rate
                })
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Performance alerts generation failed: {e}")
            return []
    
    def _calculate_revenue_distribution(self, revenues: List[float]) -> Dict[str, Any]:
        """収益分布の計算"""
        try:
            if not revenues:
                return {}
            
            sorted_revenues = sorted(revenues, reverse=True)
            total_revenue = sum(revenues)
            
            # パレート分析（80/20ルール）
            cumulative_revenue = 0
            pareto_point = 0
            
            for i, revenue in enumerate(sorted_revenues):
                cumulative_revenue += revenue
                if cumulative_revenue >= total_revenue * 0.8:
                    pareto_point = i + 1
                    break
            
            return {
                'total_affiliates': len(revenues),
                'top_20_percent_count': max(1, len(revenues) // 5),
                'pareto_point': pareto_point,
                'pareto_percentage': (pareto_point / len(revenues)) * 100,
                'revenue_concentration': (sum(sorted_revenues[:pareto_point]) / total_revenue) * 100
            }
            
        except Exception as e:
            self.logger.error(f"Revenue distribution calculation failed: {e}")
            return {}
    
    def _calculate_linear_forecast(self, daily_revenues: Dict[str, float], 
                                  days_ahead: int) -> Dict[str, float]:
        """線形予測の計算"""
        try:
            if not daily_revenues:
                return {}
            
            # 日付順でソート
            sorted_data = sorted(daily_revenues.items())
            
            # 簡単な移動平均による予測
            recent_values = [value for _, value in sorted_data[-14:]]  # 直近14日
            average_revenue = sum(recent_values) / len(recent_values) if recent_values else 0
            
            # 予測データの生成
            forecast = {}
            base_date = datetime.now(timezone.utc)
            
            for i in range(1, days_ahead + 1):
                forecast_date = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
                # 簡単な予測: 移動平均に小さなランダム要素を追加
                forecast[forecast_date] = average_revenue * (0.9 + (i % 7) * 0.02)  # 曜日効果を模擬
            
            return forecast
            
        except Exception as e:
            self.logger.error(f"Linear forecast calculation failed: {e}")
            return {}
    
    def _calculate_confidence_intervals(self, historical_data: Dict[str, float], 
                                      forecast: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """信頼区間の計算"""
        try:
            if not historical_data:
                return {}
            
            # 過去データの標準偏差を計算
            values = list(historical_data.values())
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            
            confidence_intervals = {}
            
            for date, predicted_value in forecast.items():
                confidence_intervals[date] = {
                    'lower_bound': max(0, predicted_value - 1.96 * std_dev),  # 95%信頼区間
                    'upper_bound': predicted_value + 1.96 * std_dev
                }
            
            return confidence_intervals
            
        except Exception as e:
            self.logger.error(f"Confidence intervals calculation failed: {e}")
            return {}
    
    def _calculate_growth_trend(self, daily_revenues: Dict[str, float]) -> str:
        """成長トレンドの計算"""
        try:
            if len(daily_revenues) < 7:
                return 'insufficient_data'
            
            sorted_data = sorted(daily_revenues.items())
            
            # 前半と後半の平均を比較
            mid_point = len(sorted_data) // 2
            first_half_avg = sum(value for _, value in sorted_data[:mid_point]) / mid_point
            second_half_avg = sum(value for _, value in sorted_data[mid_point:]) / (len(sorted_data) - mid_point)
            
            if second_half_avg > first_half_avg * 1.1:
                return 'growing'
            elif second_half_avg < first_half_avg * 0.9:
                return 'declining'
            else:
                return 'stable'
                
        except Exception as e:
            self.logger.error(f"Growth trend calculation failed: {e}")
            return 'unknown'
    
    def _calculate_source_conversion_rates(self, days: int) -> Dict[str, Dict[str, Any]]:
        """ソース別コンバージョン率の計算"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            click_analytics = self.affiliate_tracker.get_click_analytics(
                start_date=start_date, end_date=end_date
            )
            
            clicks_by_source = click_analytics.get('clicks_by_source', {})
            
            # 各ソースのコンバージョン数を計算
            source_conversions = {}
            
            for source in clicks_by_source.keys():
                # ソース別のコンバージョン数を取得（簡単な実装）
                conversions = self.affiliate_tracker._get_conversions_from_db(
                    start_date=start_date, end_date=end_date
                )
                
                source_conversion_count = 0
                for conversion in conversions:
                    click_info = self.affiliate_tracker._get_click_from_db(conversion.get('click_id', ''))
                    if click_info and click_info.get('source') == source:
                        source_conversion_count += 1
                
                source_conversions[source] = source_conversion_count
            
            # コンバージョン率計算
            source_performance = {}
            for source, clicks in clicks_by_source.items():
                conversions = source_conversions.get(source, 0)
                conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
                
                source_performance[source] = {
                    'clicks': clicks,
                    'conversions': conversions,
                    'conversion_rate': conversion_rate
                }
            
            return source_performance
            
        except Exception as e:
            self.logger.error(f"Source conversion rates calculation failed: {e}")
            return {}
    
    def _analyze_hourly_conversion_patterns(self, days: int) -> Dict[str, int]:
        """時間別コンバージョンパターンの分析"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            conversions = self.affiliate_tracker._get_conversions_from_db(
                start_date=start_date, end_date=end_date
            )
            
            hourly_patterns = {}
            
            for conversion in conversions:
                converted_at = datetime.fromisoformat(conversion['converted_at'].replace('Z', '+00:00'))
                hour_key = converted_at.strftime('%H:00')
                hourly_patterns[hour_key] = hourly_patterns.get(hour_key, 0) + 1
            
            return hourly_patterns
            
        except Exception as e:
            self.logger.error(f"Hourly conversion patterns analysis failed: {e}")
            return {}
    
    def _get_best_conversion_hours(self, hourly_patterns: Dict[str, int]) -> List[str]:
        """最適コンバージョン時間の取得"""
        try:
            if not hourly_patterns:
                return []
            
            # 上位3時間を取得
            sorted_hours = sorted(hourly_patterns.items(), key=lambda x: x[1], reverse=True)
            return [hour for hour, _ in sorted_hours[:3]]
            
        except Exception as e:
            self.logger.error(f"Best conversion hours calculation failed: {e}")
            return []
    
    def _calculate_conversion_velocity(self, days: int) -> Dict[str, float]:
        """コンバージョン速度の計算"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            conversions = self.affiliate_tracker._get_conversions_from_db(
                start_date=start_date, end_date=end_date
            )
            
            conversion_times = []
            
            for conversion in conversions:
                click_info = self.affiliate_tracker._get_click_from_db(conversion.get('click_id', ''))
                if click_info:
                    clicked_at = datetime.fromisoformat(click_info['clicked_at'].replace('Z', '+00:00'))
                    converted_at = datetime.fromisoformat(conversion['converted_at'].replace('Z', '+00:00'))
                    
                    time_to_conversion = (converted_at - clicked_at).total_seconds() / 3600  # 時間単位
                    conversion_times.append(time_to_conversion)
            
            if conversion_times:
                return {
                    'average_hours': statistics.mean(conversion_times),
                    'median_hours': statistics.median(conversion_times),
                    'fastest_hours': min(conversion_times),
                    'slowest_hours': max(conversion_times)
                }
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Conversion velocity calculation failed: {e}")
            return {}
    
    def _generate_optimization_recommendations(self, source_performance: Dict[str, Dict[str, Any]], 
                                             hourly_patterns: Dict[str, int]) -> List[Dict[str, str]]:
        """最適化推奨事項の生成"""
        try:
            recommendations = []
            
            # ソースパフォーマンス分析
            if source_performance:
                best_source = max(source_performance.items(), key=lambda x: x[1].get('conversion_rate', 0))
                worst_source = min(source_performance.items(), key=lambda x: x[1].get('conversion_rate', 0))
                
                if best_source[1].get('conversion_rate', 0) > worst_source[1].get('conversion_rate', 0) * 2:
                    recommendations.append({
                        'type': 'source_optimization',
                        'priority': 'high',
                        'recommendation': f'{best_source[0]}のパフォーマンスが優秀です。このソースからのトラフィックを増やすことを検討してください。'
                    })
            
            # 時間パターン分析
            if hourly_patterns:
                best_hours = self._get_best_conversion_hours(hourly_patterns)
                if best_hours:
                    recommendations.append({
                        'type': 'timing_optimization',
                        'priority': 'medium',
                        'recommendation': f'{", ".join(best_hours)}の時間帯でのコンバージョンが多いです。この時間帯にマーケティング活動を集中することを検討してください。'
                    })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Optimization recommendations generation failed: {e}")
            return []
    
    def _compare_attribution_models(self, attribution_data: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """アトリビューションモデル比較"""
        try:
            # 簡単な実装: ラストクリックモデルのみ
            last_click = attribution_data.get('last_click_attribution', {})
            
            if not last_click:
                return {}
            
            total_revenue = sum(last_click.values())
            
            comparison = {
                'model_summary': {
                    'last_click': {
                        'total_revenue': total_revenue,
                        'top_source': max(last_click.items(), key=lambda x: x[1])[0] if last_click else None
                    }
                },
                'source_comparison': last_click
            }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Attribution models comparison failed: {e}")
            return {}
    
    def _generate_attribution_insights(self, attribution_data: Dict[str, Dict[str, float]]) -> List[str]:
        """アトリビューション洞察の生成"""
        try:
            insights = []
            
            last_click = attribution_data.get('last_click_attribution', {})
            
            if last_click:
                top_source = max(last_click.items(), key=lambda x: x[1])
                total_revenue = sum(last_click.values())
                top_source_percentage = (top_source[1] / total_revenue) * 100
                
                insights.append(f'{top_source[0]}が収益の{top_source_percentage:.1f}%を占めています。')
                
                if top_source_percentage > 50:
                    insights.append('単一ソースへの依存度が高いです。リスク分散を検討してください。')
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Attribution insights generation failed: {e}")
            return []