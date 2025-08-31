"""
Enhanced Affiliate Reports - 強化されたアフィリエイトレポートシステム
詳細な分析、予測、最適化提案機能を提供
"""
import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import statistics
import math


@dataclass
class RevenueProjection:
    """収益予測データ"""
    period: str
    projected_revenue: float
    confidence_interval: Tuple[float, float]
    growth_rate: float
    factors: List[str]


@dataclass
class OptimizationRecommendation:
    """最適化提案"""
    category: str
    priority: str  # high, medium, low
    title: str
    description: str
    expected_impact: str
    implementation_effort: str
    metrics_to_track: List[str]


class EnhancedAffiliateReports:
    """強化されたアフィリエイトレポートシステム"""
    
    def __init__(self, affiliate_tracker, db_manager=None, cache_manager=None):
        self.tracker = affiliate_tracker
        self.db = db_manager
        self.cache = cache_manager
        self.logger = logging.getLogger(__name__)
        
        # 分析設定
        self.analysis_periods = {
            'daily': 1,
            'weekly': 7,
            'monthly': 30,
            'quarterly': 90,
            'yearly': 365
        }
        
        # 予測モデル設定
        self.prediction_models = ['linear', 'exponential', 'seasonal']
        self.confidence_levels = [0.8, 0.9, 0.95]
        
        # 最適化カテゴリ
        self.optimization_categories = [
            'conversion_rate',
            'click_quality',
            'resource_placement',
            'timing_optimization',
            'audience_targeting',
            'partner_selection'
        ]
    
    def generate_comprehensive_report(self, affiliate_id: str = None,
                                   period: str = 'monthly') -> Dict[str, Any]:
        """包括的なアフィリエイトレポートの生成"""
        try:
            end_date = datetime.now(timezone.utc)
            days = self.analysis_periods.get(period, 30)
            start_date = end_date - timedelta(days=days)
            
            # 基本データの取得
            clicks = self.tracker._get_clicks_from_db(affiliate_id, start_date, end_date)
            conversions = self.tracker._get_conversions_from_db(affiliate_id, start_date, end_date)
            
            # 包括的レポートの構築
            report = {
                'report_metadata': {
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                    'period': period,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'affiliate_id': affiliate_id,
                    'total_data_points': len(clicks) + len(conversions)
                },
                'executive_summary': self._generate_executive_summary(clicks, conversions),
                'performance_metrics': self._calculate_advanced_metrics(clicks, conversions),
                'trend_analysis': self._analyze_trends(clicks, conversions, period),
                'conversion_analysis': self._analyze_conversions(clicks, conversions),
                'revenue_analysis': self._analyze_revenue(conversions),
                'quality_metrics': self._calculate_quality_metrics(clicks, conversions),
                'competitive_analysis': self._generate_competitive_analysis(affiliate_id),
                'projections': self._generate_revenue_projections(conversions, period),
                'optimization_recommendations': self._generate_optimization_recommendations(
                    clicks, conversions, affiliate_id
                ),
                'actionable_insights': self._generate_actionable_insights(clicks, conversions)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Comprehensive report generation failed: {e}")
            return {}
    
    def _generate_executive_summary(self, clicks: List[Dict], conversions: List[Dict]) -> Dict[str, Any]:
        """エグゼクティブサマリーの生成"""
        try:
            total_clicks = len(clicks)
            total_conversions = len(conversions)
            total_revenue = sum(self.tracker._calculate_revenue_from_conversion(c) for c in conversions)
            
            conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
            avg_order_value = total_revenue / total_conversions if total_conversions > 0 else 0
            revenue_per_click = total_revenue / total_clicks if total_clicks > 0 else 0
            
            # 前期比較（簡易版）
            previous_period_data = self._get_previous_period_data(clicks, conversions)
            growth_metrics = self._calculate_growth_metrics(
                {
                    'clicks': total_clicks,
                    'conversions': total_conversions,
                    'revenue': total_revenue
                },
                previous_period_data
            )
            
            return {
                'key_metrics': {
                    'total_clicks': total_clicks,
                    'total_conversions': total_conversions,
                    'conversion_rate': round(conversion_rate, 2),
                    'total_revenue': round(total_revenue, 2),
                    'average_order_value': round(avg_order_value, 2),
                    'revenue_per_click': round(revenue_per_click, 4)
                },
                'growth_metrics': growth_metrics,
                'performance_status': self._determine_performance_status(conversion_rate, total_revenue),
                'top_highlights': self._generate_top_highlights(clicks, conversions),
                'areas_for_improvement': self._identify_improvement_areas(clicks, conversions)
            }
            
        except Exception as e:
            self.logger.error(f"Executive summary generation failed: {e}")
            return {}    d
ef _calculate_advanced_metrics(self, clicks: List[Dict], conversions: List[Dict]) -> Dict[str, Any]:
        """高度なパフォーマンスメトリクスの計算"""
        try:
            # 基本メトリクス
            total_clicks = len(clicks)
            total_conversions = len(conversions)
            
            # 時間ベースメトリクス
            time_to_conversion = []
            for conversion in conversions:
                click_id = conversion.get('click_id')
                if click_id:
                    click_info = next((c for c in clicks if c.get('click_id') == click_id), None)
                    if click_info:
                        click_time = datetime.fromisoformat(click_info['clicked_at'].replace('Z', '+00:00'))
                        conv_time = datetime.fromisoformat(conversion['converted_at'].replace('Z', '+00:00'))
                        time_diff = (conv_time - click_time).total_seconds() / 3600  # 時間単位
                        time_to_conversion.append(time_diff)
            
            # 品質メトリクス
            quality_scores = []
            for click in clicks:
                metadata = json.loads(click.get('metadata', '{}'))
                quality_score = metadata.get('click_quality_score', 0.5)
                quality_scores.append(quality_score)
            
            # ユーザーエンゲージメント
            unique_users = len(set(c.get('user_id') for c in clicks if c.get('user_id')))
            repeat_users = total_clicks - unique_users if unique_users <= total_clicks else 0
            
            return {
                'engagement_metrics': {
                    'unique_users': unique_users,
                    'repeat_users': repeat_users,
                    'clicks_per_user': round(total_clicks / unique_users, 2) if unique_users > 0 else 0,
                    'user_retention_rate': round(repeat_users / unique_users * 100, 2) if unique_users > 0 else 0
                },
                'timing_metrics': {
                    'average_time_to_conversion_hours': round(statistics.mean(time_to_conversion), 2) if time_to_conversion else 0,
                    'median_time_to_conversion_hours': round(statistics.median(time_to_conversion), 2) if time_to_conversion else 0,
                    'fastest_conversion_hours': round(min(time_to_conversion), 2) if time_to_conversion else 0,
                    'slowest_conversion_hours': round(max(time_to_conversion), 2) if time_to_conversion else 0
                },
                'quality_metrics': {
                    'average_click_quality': round(statistics.mean(quality_scores), 3) if quality_scores else 0,
                    'quality_distribution': self._calculate_quality_distribution(quality_scores),
                    'high_quality_click_rate': round(len([q for q in quality_scores if q > 0.7]) / len(quality_scores) * 100, 2) if quality_scores else 0
                },
                'conversion_efficiency': {
                    'conversion_velocity': self._calculate_conversion_velocity(conversions),
                    'conversion_consistency': self._calculate_conversion_consistency(conversions),
                    'peak_conversion_hours': self._identify_peak_conversion_hours(conversions)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Advanced metrics calculation failed: {e}")
            return {}
    
    def _analyze_trends(self, clicks: List[Dict], conversions: List[Dict], period: str) -> Dict[str, Any]:
        """トレンド分析"""
        try:
            # 日別データの集計
            daily_data = {}
            
            # クリックの日別集計
            for click in clicks:
                clicked_at = datetime.fromisoformat(click['clicked_at'].replace('Z', '+00:00'))
                date_key = clicked_at.strftime('%Y-%m-%d')
                if date_key not in daily_data:
                    daily_data[date_key] = {'clicks': 0, 'conversions': 0, 'revenue': 0}
                daily_data[date_key]['clicks'] += 1
            
            # コンバージョンの日別集計
            for conversion in conversions:
                converted_at = datetime.fromisoformat(conversion['converted_at'].replace('Z', '+00:00'))
                date_key = converted_at.strftime('%Y-%m-%d')
                if date_key not in daily_data:
                    daily_data[date_key] = {'clicks': 0, 'conversions': 0, 'revenue': 0}
                daily_data[date_key]['conversions'] += 1
                daily_data[date_key]['revenue'] += self.tracker._calculate_revenue_from_conversion(conversion)
            
            # トレンド計算
            sorted_dates = sorted(daily_data.keys())
            
            clicks_trend = [daily_data[date]['clicks'] for date in sorted_dates]
            conversions_trend = [daily_data[date]['conversions'] for date in sorted_dates]
            revenue_trend = [daily_data[date]['revenue'] for date in sorted_dates]
            
            return {
                'daily_breakdown': daily_data,
                'trend_analysis': {
                    'clicks_trend': {
                        'data': clicks_trend,
                        'direction': self._calculate_trend_direction(clicks_trend),
                        'volatility': self._calculate_volatility(clicks_trend),
                        'growth_rate': self._calculate_growth_rate(clicks_trend)
                    },
                    'conversions_trend': {
                        'data': conversions_trend,
                        'direction': self._calculate_trend_direction(conversions_trend),
                        'volatility': self._calculate_volatility(conversions_trend),
                        'growth_rate': self._calculate_growth_rate(conversions_trend)
                    },
                    'revenue_trend': {
                        'data': revenue_trend,
                        'direction': self._calculate_trend_direction(revenue_trend),
                        'volatility': self._calculate_volatility(revenue_trend),
                        'growth_rate': self._calculate_growth_rate(revenue_trend)
                    }
                },
                'seasonal_patterns': self._identify_seasonal_patterns(daily_data, period),
                'anomaly_detection': self._detect_anomalies(daily_data)
            }
            
        except Exception as e:
            self.logger.error(f"Trend analysis failed: {e}")
            return {}
    
    def _generate_optimization_recommendations(self, clicks: List[Dict], 
                                            conversions: List[Dict], 
                                            affiliate_id: str = None) -> List[OptimizationRecommendation]:
        """最適化提案の生成"""
        try:
            recommendations = []
            
            # コンバージョン率の分析
            total_clicks = len(clicks)
            total_conversions = len(conversions)
            conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
            
            if conversion_rate < 2.0:  # 業界平均を下回る場合
                recommendations.append(OptimizationRecommendation(
                    category='conversion_rate',
                    priority='high',
                    title='コンバージョン率の改善',
                    description=f'現在のコンバージョン率({conversion_rate:.2f}%)は業界平均を下回っています。ランディングページの最適化、CTAの改善、ターゲティングの見直しを推奨します。',
                    expected_impact='コンバージョン率20-50%向上',
                    implementation_effort='medium',
                    metrics_to_track=['conversion_rate', 'bounce_rate', 'time_on_page']
                ))
            
            # クリック品質の分析
            quality_scores = []
            for click in clicks:
                metadata = json.loads(click.get('metadata', '{}'))
                quality_score = metadata.get('click_quality_score', 0.5)
                quality_scores.append(quality_score)
            
            avg_quality = statistics.mean(quality_scores) if quality_scores else 0
            if avg_quality < 0.6:
                recommendations.append(OptimizationRecommendation(
                    category='click_quality',
                    priority='medium',
                    title='クリック品質の向上',
                    description=f'平均クリック品質スコア({avg_quality:.2f})が低いです。より関連性の高いコンテンツの配置、ユーザーセグメンテーションの改善を推奨します。',
                    expected_impact='クリック品質15-30%向上',
                    implementation_effort='low',
                    metrics_to_track=['click_quality_score', 'engagement_rate', 'return_visitor_rate']
                ))
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Optimization recommendations generation failed: {e}")
            return []
    
    def export_report_to_json(self, report: Dict[str, Any], filename: str = None) -> str:
        """レポートをJSONファイルにエクスポート"""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"affiliate_report_{timestamp}.json"
            
            filepath = os.path.join('reports', filename)
            os.makedirs('reports', exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"Report exported to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Report export failed: {e}")
            return ""
    
    # ヘルパーメソッド
    def _calculate_trend_direction(self, data: List[float]) -> str:
        """トレンド方向の計算"""
        if len(data) < 2:
            return 'insufficient_data'
        
        # 線形回帰の傾きを計算
        n = len(data)
        x = list(range(n))
        
        sum_x = sum(x)
        sum_y = sum(data)
        sum_xy = sum(x[i] * data[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_volatility(self, data: List[float]) -> float:
        """ボラティリティの計算"""
        if len(data) < 2:
            return 0.0
        
        mean_val = statistics.mean(data)
        variance = statistics.variance(data)
        
        return math.sqrt(variance) / mean_val if mean_val > 0 else 0.0
    
    def _calculate_growth_rate(self, data: List[float]) -> float:
        """成長率の計算"""
        if len(data) < 2:
            return 0.0
        
        return ((data[-1] - data[0]) / data[0] * 100) if data[0] > 0 else 0.0
    
    # 簡易実装のヘルパーメソッド
    def _get_previous_period_data(self, clicks: List[Dict], conversions: List[Dict]) -> Dict[str, Any]:
        return {'clicks': 0, 'conversions': 0, 'revenue': 0}
    
    def _calculate_growth_metrics(self, current: Dict, previous: Dict) -> Dict[str, Any]:
        return {'clicks_growth': 0, 'conversions_growth': 0, 'revenue_growth': 0}
    
    def _determine_performance_status(self, conversion_rate: float, revenue: float) -> str:
        if conversion_rate > 3.0 and revenue > 1000:
            return 'excellent'
        elif conversion_rate > 2.0 and revenue > 500:
            return 'good'
        elif conversion_rate > 1.0 and revenue > 100:
            return 'average'
        else:
            return 'needs_improvement'
    
    def _generate_top_highlights(self, clicks: List[Dict], conversions: List[Dict]) -> List[str]:
        return [f"総クリック数: {len(clicks)}", f"総コンバージョン数: {len(conversions)}"]
    
    def _identify_improvement_areas(self, clicks: List[Dict], conversions: List[Dict]) -> List[str]:
        return ["コンバージョン率の最適化", "クリック品質の向上"]
    
    def _calculate_quality_distribution(self, quality_scores: List[float]) -> Dict[str, int]:
        if not quality_scores:
            return {}
        
        distribution = {'high': 0, 'medium': 0, 'low': 0}
        for score in quality_scores:
            if score > 0.7:
                distribution['high'] += 1
            elif score > 0.4:
                distribution['medium'] += 1
            else:
                distribution['low'] += 1
        
        return distribution
    
    def _calculate_conversion_velocity(self, conversions: List[Dict]) -> float:
        return 0.0  # 簡易実装
    
    def _calculate_conversion_consistency(self, conversions: List[Dict]) -> float:
        return 1.0  # 簡易実装
    
    def _identify_peak_conversion_hours(self, conversions: List[Dict]) -> List[int]:
        return []  # 簡易実装
    
    def _analyze_conversions(self, clicks: List[Dict], conversions: List[Dict]) -> Dict[str, Any]:
        return {'analysis': 'conversion_analysis_placeholder'}
    
    def _analyze_revenue(self, conversions: List[Dict]) -> Dict[str, Any]:
        return {'analysis': 'revenue_analysis_placeholder'}
    
    def _calculate_quality_metrics(self, clicks: List[Dict], conversions: List[Dict]) -> Dict[str, Any]:
        return {'metrics': 'quality_metrics_placeholder'}
    
    def _generate_competitive_analysis(self, affiliate_id: str) -> Dict[str, Any]:
        return {'analysis': 'competitive_analysis_placeholder'}
    
    def _generate_revenue_projections(self, conversions: List[Dict], period: str) -> Dict[str, Any]:
        return {'projections': 'revenue_projections_placeholder'}
    
    def _generate_actionable_insights(self, clicks: List[Dict], conversions: List[Dict]) -> List[Dict[str, Any]]:
        return []
    
    def _identify_seasonal_patterns(self, daily_data: Dict, period: str) -> Dict[str, Any]:
        return {'pattern_detected': False}
    
    def _detect_anomalies(self, daily_data: Dict) -> List[Dict[str, Any]]:
        return []