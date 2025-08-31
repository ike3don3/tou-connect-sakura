"""
AffiliateTracker - アフィリエイト追跡システム
クリック追跡、コンバージョン追跡、収益計算機能
"""
import os
import json
import time
import logging
import hashlib
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid


class ClickSource(Enum):
    """クリックソース"""
    LEARNING_RESOURCES = "learning_resources"
    MATCHING_RESULTS = "matching_results"
    RECOMMENDATIONS = "recommendations"
    SEARCH_RESULTS = "search_results"
    PROFILE_PAGE = "profile_page"


class ConversionType(Enum):
    """コンバージョンタイプ"""
    PURCHASE = "purchase"
    SIGNUP = "signup"
    DOWNLOAD = "download"
    SUBSCRIPTION = "subscription"
    COURSE_ENROLLMENT = "course_enrollment"


@dataclass
class AffiliateClick:
    """アフィリエイトクリック情報"""
    click_id: str
    user_id: Optional[int]
    session_id: str
    affiliate_id: str
    resource_id: str
    resource_url: str
    source: ClickSource
    clicked_at: datetime
    ip_address: str
    user_agent: str
    referrer: str
    metadata: Dict[str, Any]


@dataclass
class AffiliateConversion:
    """アフィリエイトコンバージョン情報"""
    conversion_id: str
    click_id: str
    user_id: Optional[int]
    affiliate_id: str
    conversion_type: ConversionType
    conversion_value: float
    currency: str
    converted_at: datetime
    metadata: Dict[str, Any]


class AffiliateTracker:
    """アフィリエイト追跡システム（強化版）"""
    
    def __init__(self, db_manager=None, cache_manager=None, monitoring_manager=None):
        self.db = db_manager
        self.cache = cache_manager
        self.monitoring = monitoring_manager
        self.logger = logging.getLogger(__name__)
        
        # 設定
        self.click_expiry_hours = 24  # クリック有効期限
        self.conversion_window_days = 30  # コンバージョン追跡期間
        
        # 強化された追跡設定
        self.fraud_detection_enabled = True
        self.duplicate_click_window = 300  # 5分以内の重複クリック検出
        self.conversion_attribution_models = ['first_click', 'last_click', 'linear', 'time_decay']
        self.revenue_sharing_tiers = {
            'bronze': {'min_revenue': 0, 'bonus_rate': 0.0},
            'silver': {'min_revenue': 10000, 'bonus_rate': 0.05},
            'gold': {'min_revenue': 50000, 'bonus_rate': 0.10},
            'platinum': {'min_revenue': 100000, 'bonus_rate': 0.15}
        }
        
        # アフィリエイトパートナー設定
        self.affiliate_partners = {
            'udemy': {
                'name': 'Udemy',
                'base_url': 'https://www.udemy.com',
                'commission_rate': 0.15,
                'tracking_param': 'couponCode'
            },
            'coursera': {
                'name': 'Coursera',
                'base_url': 'https://www.coursera.org',
                'commission_rate': 0.20,
                'tracking_param': 'aid'
            },
            'amazon': {
                'name': 'Amazon',
                'base_url': 'https://amazon.co.jp',
                'commission_rate': 0.08,
                'tracking_param': 'tag'
            }
        }
        
        # 統計情報
        self.stats = {
            'total_clicks': 0,
            'total_conversions': 0,
            'total_revenue': 0.0,
            'conversion_rate': 0.0
        }
    
    def track_click(self, user_id: Optional[int], session_id: str, 
                   affiliate_id: str, resource_id: str, resource_url: str,
                   source: ClickSource, request_info: Dict[str, Any]) -> str:
        """クリック追跡（精度向上版）"""
        try:
            # 不正検出チェック
            if self.fraud_detection_enabled:
                fraud_score = self._calculate_fraud_score(user_id, session_id, request_info)
                if fraud_score > 0.8:  # 高い不正スコア
                    self.logger.warning(f"Suspicious click detected: fraud_score={fraud_score}")
                    if self.monitoring:
                        self.monitoring.record_counter("affiliate.fraud.detected", 1)
                    return resource_url  # 追跡せずに元のURLを返す
            
            # 重複クリック検出
            if self._is_duplicate_click(user_id, session_id, affiliate_id, resource_id, request_info):
                self.logger.info(f"Duplicate click detected for user {user_id}")
                if self.monitoring:
                    self.monitoring.record_counter("affiliate.clicks.duplicate", 1)
                return resource_url  # 重複の場合は追跡しない
            
            # クリックIDの生成（より安全な方法）
            click_id = self._generate_secure_click_id(user_id, session_id, affiliate_id)
            
            # 地理的情報の取得
            geo_info = self._get_geo_info(request_info.get('ip_address', ''))
            
            # デバイス情報の解析
            device_info = self._parse_device_info(request_info.get('user_agent', ''))
            
            # 強化されたメタデータ
            enhanced_metadata = {
                **request_info.get('metadata', {}),
                'geo_info': geo_info,
                'device_info': device_info,
                'fraud_score': self._calculate_fraud_score(user_id, session_id, request_info),
                'click_quality_score': self._calculate_click_quality_score(request_info),
                'attribution_weight': 1.0  # デフォルト重み
            }
            
            # クリック情報の作成
            click = AffiliateClick(
                click_id=click_id,
                user_id=user_id,
                session_id=session_id,
                affiliate_id=affiliate_id,
                resource_id=resource_id,
                resource_url=resource_url,
                source=source,
                clicked_at=datetime.now(timezone.utc),
                ip_address=request_info.get('ip_address', ''),
                user_agent=request_info.get('user_agent', ''),
                referrer=request_info.get('referrer', ''),
                metadata=enhanced_metadata
            )
            
            # データベースに保存
            if self.db:
                self._save_click_to_db(click)
            
            # キャッシュに保存（高速アクセス用）
            if self.cache:
                cache_key = f"affiliate_click:{click_id}"
                self.cache.set(cache_key, asdict(click), ttl=self.click_expiry_hours * 3600)
            
            # 追跡URLの生成
            tracking_url = self._generate_tracking_url(click)
            
            # 統計更新
            self.stats['total_clicks'] += 1
            
            # 監視メトリクス記録
            if self.monitoring:
                self.monitoring.record_counter("affiliate.clicks.total", 1, {
                    'affiliate_id': affiliate_id,
                    'source': source.value
                })
            
            self.logger.info(f"Affiliate click tracked: {click_id} for {affiliate_id}")
            
            return tracking_url
            
        except Exception as e:
            self.logger.error(f"Click tracking failed: {e}")
            return resource_url  # フォールバック: 元のURL
    
    def track_conversion(self, click_id: str, conversion_type: ConversionType,
                        conversion_value: float, currency: str = 'JPY',
                        metadata: Dict[str, Any] = None) -> bool:
        """コンバージョン追跡（強化版）"""
        try:
            # クリック情報の取得
            click_info = self._get_click_info(click_id)
            if not click_info:
                self.logger.warning(f"Click not found for conversion: {click_id}")
                return False
            
            # コンバージョン期間チェック
            click_time = datetime.fromisoformat(click_info['clicked_at'].replace('Z', '+00:00'))
            time_since_click = datetime.now(timezone.utc) - click_time
            
            if time_since_click > timedelta(days=self.conversion_window_days):
                self.logger.warning(f"Conversion window expired for click: {click_id}")
                return False
            
            # 重複コンバージョンチェック
            if self._is_duplicate_conversion(click_id, conversion_type):
                self.logger.warning(f"Duplicate conversion detected for click: {click_id}")
                return False
            
            # コンバージョン妥当性チェック
            if not self._validate_conversion(click_info, conversion_value, conversion_type):
                self.logger.warning(f"Invalid conversion detected for click: {click_id}")
                return False
            
            # コンバージョンIDの生成
            conversion_id = str(uuid.uuid4())
            
            # アトリビューション重みの計算
            attribution_weights = self._calculate_attribution_weights(click_info, time_since_click)
            
            # 強化されたメタデータ
            enhanced_metadata = {
                **(metadata or {}),
                'time_to_conversion_hours': time_since_click.total_seconds() / 3600,
                'attribution_weights': attribution_weights,
                'conversion_quality_score': self._calculate_conversion_quality_score(
                    click_info, conversion_value, time_since_click
                ),
                'revenue_tier': self._get_revenue_tier(click_info['affiliate_id']),
                'conversion_path': self._get_conversion_path(click_info.get('user_id'))
            }
            
            # コンバージョン情報の作成
            conversion = AffiliateConversion(
                conversion_id=conversion_id,
                click_id=click_id,
                user_id=click_info.get('user_id'),
                affiliate_id=click_info['affiliate_id'],
                conversion_type=conversion_type,
                conversion_value=conversion_value,
                currency=currency,
                converted_at=datetime.now(timezone.utc),
                metadata=enhanced_metadata
            )
            
            # データベースに保存
            if self.db:
                self._save_conversion_to_db(conversion)
            
            # 収益計算
            revenue = self._calculate_revenue(conversion)
            
            # 統計更新
            self.stats['total_conversions'] += 1
            self.stats['total_revenue'] += revenue
            self._update_conversion_rate()
            
            # 監視メトリクス記録
            if self.monitoring:
                self.monitoring.record_counter("affiliate.conversions.total", 1, {
                    'affiliate_id': click_info['affiliate_id'],
                    'conversion_type': conversion_type.value
                })
                self.monitoring.record_gauge("affiliate.revenue.total", revenue)
            
            self.logger.info(f"Conversion tracked: {conversion_id} for {click_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Conversion tracking failed: {e}")
            return False  
  
    def get_click_analytics(self, affiliate_id: str = None, 
                           start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """クリック分析データの取得"""
        try:
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)
            
            # データベースからクリックデータを取得
            clicks = self._get_clicks_from_db(affiliate_id, start_date, end_date)
            
            # 分析データの計算
            analytics = {
                'total_clicks': len(clicks),
                'unique_users': len(set(c.get('user_id') for c in clicks if c.get('user_id'))),
                'clicks_by_source': {},
                'clicks_by_hour': {},
                'clicks_by_day': {},
                'top_resources': {},
                'conversion_funnel': self._calculate_conversion_funnel(clicks)
            }
            
            # ソース別集計
            for click in clicks:
                source = click.get('source', 'unknown')
                analytics['clicks_by_source'][source] = analytics['clicks_by_source'].get(source, 0) + 1
            
            # 時間別集計
            for click in clicks:
                clicked_at = datetime.fromisoformat(click['clicked_at'].replace('Z', '+00:00'))
                hour_key = clicked_at.strftime('%H:00')
                analytics['clicks_by_hour'][hour_key] = analytics['clicks_by_hour'].get(hour_key, 0) + 1
            
            # 日別集計
            for click in clicks:
                clicked_at = datetime.fromisoformat(click['clicked_at'].replace('Z', '+00:00'))
                day_key = clicked_at.strftime('%Y-%m-%d')
                analytics['clicks_by_day'][day_key] = analytics['clicks_by_day'].get(day_key, 0) + 1
            
            # リソース別集計
            for click in clicks:
                resource_id = click.get('resource_id', 'unknown')
                analytics['top_resources'][resource_id] = analytics['top_resources'].get(resource_id, 0) + 1
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Click analytics failed: {e}")
            return {}
    
    def get_revenue_report(self, affiliate_id: str = None,
                          start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """収益レポートの生成"""
        try:
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)
            
            # コンバージョンデータの取得
            conversions = self._get_conversions_from_db(affiliate_id, start_date, end_date)
            
            # 収益計算
            total_revenue = sum(self._calculate_revenue_from_conversion(c) for c in conversions)
            total_conversions = len(conversions)
            
            # 収益レポート
            report = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_revenue': total_revenue,
                    'total_conversions': total_conversions,
                    'average_order_value': total_revenue / total_conversions if total_conversions > 0 else 0,
                    'conversion_rate': self._calculate_conversion_rate(affiliate_id, start_date, end_date)
                },
                'revenue_by_affiliate': {},
                'revenue_by_type': {},
                'revenue_by_day': {},
                'top_performing_resources': self._get_top_performing_resources(conversions)
            }
            
            # アフィリエイト別収益
            for conversion in conversions:
                affiliate = conversion.get('affiliate_id', 'unknown')
                revenue = self._calculate_revenue_from_conversion(conversion)
                report['revenue_by_affiliate'][affiliate] = report['revenue_by_affiliate'].get(affiliate, 0) + revenue
            
            # タイプ別収益
            for conversion in conversions:
                conv_type = conversion.get('conversion_type', 'unknown')
                revenue = self._calculate_revenue_from_conversion(conversion)
                report['revenue_by_type'][conv_type] = report['revenue_by_type'].get(conv_type, 0) + revenue
            
            # 日別収益
            for conversion in conversions:
                converted_at = datetime.fromisoformat(conversion['converted_at'].replace('Z', '+00:00'))
                day_key = converted_at.strftime('%Y-%m-%d')
                revenue = self._calculate_revenue_from_conversion(conversion)
                report['revenue_by_day'][day_key] = report['revenue_by_day'].get(day_key, 0) + revenue
            
            return report
            
        except Exception as e:
            self.logger.error(f"Revenue report generation failed: {e}")
            return {}
    
    def get_affiliate_performance(self, affiliate_id: str) -> Dict[str, Any]:
        """アフィリエイトパフォーマンスの取得"""
        try:
            # 30日間のデータを取得
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=30)
            
            clicks = self._get_clicks_from_db(affiliate_id, start_date, end_date)
            conversions = self._get_conversions_from_db(affiliate_id, start_date, end_date)
            
            total_clicks = len(clicks)
            total_conversions = len(conversions)
            total_revenue = sum(self._calculate_revenue_from_conversion(c) for c in conversions)
            
            performance = {
                'affiliate_id': affiliate_id,
                'affiliate_name': self.affiliate_partners.get(affiliate_id, {}).get('name', affiliate_id),
                'period_days': 30,
                'metrics': {
                    'total_clicks': total_clicks,
                    'total_conversions': total_conversions,
                    'conversion_rate': (total_conversions / total_clicks * 100) if total_clicks > 0 else 0,
                    'total_revenue': total_revenue,
                    'revenue_per_click': total_revenue / total_clicks if total_clicks > 0 else 0,
                    'average_order_value': total_revenue / total_conversions if total_conversions > 0 else 0
                },
                'trends': {
                    'clicks_trend': self._calculate_trend(clicks, 'clicked_at'),
                    'conversions_trend': self._calculate_trend(conversions, 'converted_at'),
                    'revenue_trend': self._calculate_revenue_trend(conversions)
                }
            }
            
            return performance
            
        except Exception as e:
            self.logger.error(f"Affiliate performance calculation failed: {e}")
            return {}
    
    def _generate_tracking_url(self, click: AffiliateClick) -> str:
        """追跡URL生成"""
        try:
            partner_config = self.affiliate_partners.get(click.affiliate_id, {})
            if not partner_config:
                return click.resource_url
            
            # 追跡パラメータの追加
            parsed_url = urllib.parse.urlparse(click.resource_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # アフィリエイト追跡パラメータを追加
            tracking_param = partner_config.get('tracking_param', 'ref')
            query_params[tracking_param] = [f"tou_connect_{click.click_id}"]
            
            # UTMパラメータの追加
            query_params['utm_source'] = ['tou_connect']
            query_params['utm_medium'] = ['affiliate']
            query_params['utm_campaign'] = [click.source.value]
            query_params['utm_content'] = [click.resource_id]
            
            # URLの再構築
            new_query = urllib.parse.urlencode(query_params, doseq=True)
            tracking_url = urllib.parse.urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))
            
            return tracking_url
            
        except Exception as e:
            self.logger.error(f"Tracking URL generation failed: {e}")
            return click.resource_url
    
    def _calculate_revenue(self, conversion: AffiliateConversion) -> float:
        """収益計算"""
        try:
            partner_config = self.affiliate_partners.get(conversion.affiliate_id, {})
            commission_rate = partner_config.get('commission_rate', 0.1)
            
            return conversion.conversion_value * commission_rate
            
        except Exception as e:
            self.logger.error(f"Revenue calculation failed: {e}")
            return 0.0
    
    def _calculate_revenue_from_conversion(self, conversion_data: Dict[str, Any]) -> float:
        """コンバージョンデータから収益計算"""
        try:
            affiliate_id = conversion_data.get('affiliate_id', '')
            conversion_value = conversion_data.get('conversion_value', 0.0)
            
            partner_config = self.affiliate_partners.get(affiliate_id, {})
            commission_rate = partner_config.get('commission_rate', 0.1)
            
            return conversion_value * commission_rate
            
        except Exception as e:
            self.logger.error(f"Revenue calculation from conversion data failed: {e}")
            return 0.0
    
    def _update_conversion_rate(self):
        """コンバージョン率の更新"""
        if self.stats['total_clicks'] > 0:
            self.stats['conversion_rate'] = (self.stats['total_conversions'] / self.stats['total_clicks']) * 100
        else:
            self.stats['conversion_rate'] = 0.0
    
    def _get_click_info(self, click_id: str) -> Optional[Dict[str, Any]]:
        """クリック情報の取得"""
        try:
            # キャッシュから取得を試行
            if self.cache:
                cache_key = f"affiliate_click:{click_id}"
                cached_click = self.cache.get(cache_key)
                if cached_click:
                    return cached_click
            
            # データベースから取得
            if self.db:
                return self._get_click_from_db(click_id)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Click info retrieval failed: {e}")
            return None
    
    def _save_click_to_db(self, click: AffiliateClick):
        """クリック情報をデータベースに保存"""
        try:
            if not self.db:
                return
            
            sql = """
            INSERT INTO affiliate_clicks 
            (click_id, user_id, session_id, affiliate_id, resource_id, resource_url, 
             source, clicked_at, ip_address, user_agent, referrer, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                click.click_id,
                click.user_id,
                click.session_id,
                click.affiliate_id,
                click.resource_id,
                click.resource_url,
                click.source.value,
                click.clicked_at,
                click.ip_address,
                click.user_agent,
                click.referrer,
                json.dumps(click.metadata)
            )
            
            if hasattr(self.db, 'execute_with_retry'):
                self.db.execute_with_retry(sql, params)
            else:
                self.db.execute(sql, params)
                
        except Exception as e:
            self.logger.error(f"Click save to DB failed: {e}")
    
    def _save_conversion_to_db(self, conversion: AffiliateConversion):
        """コンバージョン情報をデータベースに保存"""
        try:
            if not self.db:
                return
            
            sql = """
            INSERT INTO affiliate_conversions 
            (conversion_id, click_id, user_id, affiliate_id, conversion_type, 
             conversion_value, currency, converted_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                conversion.conversion_id,
                conversion.click_id,
                conversion.user_id,
                conversion.affiliate_id,
                conversion.conversion_type.value,
                conversion.conversion_value,
                conversion.currency,
                conversion.converted_at,
                json.dumps(conversion.metadata)
            )
            
            if hasattr(self.db, 'execute_with_retry'):
                self.db.execute_with_retry(sql, params)
            else:
                self.db.execute(sql, params)
                
        except Exception as e:
            self.logger.error(f"Conversion save to DB failed: {e}")
    
    def _get_click_from_db(self, click_id: str) -> Optional[Dict[str, Any]]:
        """データベースからクリック情報を取得"""
        try:
            sql = "SELECT * FROM affiliate_clicks WHERE click_id = ?"
            
            if hasattr(self.db, 'fetch_one_with_retry'):
                return self.db.fetch_one_with_retry(sql, (click_id,))
            else:
                cursor = self.db.connection.execute(sql, (click_id,))
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
                
        except Exception as e:
            self.logger.error(f"Click retrieval from DB failed: {e}")
            return None
    
    def _get_clicks_from_db(self, affiliate_id: str = None, 
                           start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """データベースからクリック一覧を取得"""
        try:
            sql = "SELECT * FROM affiliate_clicks WHERE 1=1"
            params = []
            
            if affiliate_id:
                sql += " AND affiliate_id = ?"
                params.append(affiliate_id)
            
            if start_date:
                sql += " AND clicked_at >= ?"
                params.append(start_date)
            
            if end_date:
                sql += " AND clicked_at <= ?"
                params.append(end_date)
            
            sql += " ORDER BY clicked_at DESC"
            
            if hasattr(self.db, 'fetch_all_with_retry'):
                return self.db.fetch_all_with_retry(sql, params)
            else:
                cursor = self.db.connection.execute(sql, params)
                rows = cursor.fetchall()
                if rows:
                    columns = [description[0] for description in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
                return []
                
        except Exception as e:
            self.logger.error(f"Clicks retrieval from DB failed: {e}")
            return []
    
    def _get_conversions_from_db(self, affiliate_id: str = None,
                                start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """データベースからコンバージョン一覧を取得"""
        try:
            sql = "SELECT * FROM affiliate_conversions WHERE 1=1"
            params = []
            
            if affiliate_id:
                sql += " AND affiliate_id = ?"
                params.append(affiliate_id)
            
            if start_date:
                sql += " AND converted_at >= ?"
                params.append(start_date)
            
            if end_date:
                sql += " AND converted_at <= ?"
                params.append(end_date)
            
            sql += " ORDER BY converted_at DESC"
            
            if hasattr(self.db, 'fetch_all_with_retry'):
                return self.db.fetch_all_with_retry(sql, params)
            else:
                cursor = self.db.connection.execute(sql, params)
                rows = cursor.fetchall()
                if rows:
                    columns = [description[0] for description in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
                return []
                
        except Exception as e:
            self.logger.error(f"Conversions retrieval from DB failed: {e}")
            return []
    
    def _calculate_conversion_funnel(self, clicks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """コンバージョンファネルの計算"""
        try:
            # 簡単な実装: クリック数とコンバージョン数の比較
            total_clicks = len(clicks)
            
            # 対応するコンバージョンを取得
            click_ids = [c.get('click_id') for c in clicks if c.get('click_id')]
            conversions = []
            
            for click_id in click_ids:
                conv_sql = "SELECT * FROM affiliate_conversions WHERE click_id = ?"
                if hasattr(self.db, 'fetch_all_with_retry'):
                    conv_results = self.db.fetch_all_with_retry(conv_sql, (click_id,))
                    conversions.extend(conv_results)
            
            total_conversions = len(conversions)
            
            return {
                'total_clicks': total_clicks,
                'total_conversions': total_conversions,
                'conversion_rate': (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Conversion funnel calculation failed: {e}")
            return {'total_clicks': 0, 'total_conversions': 0, 'conversion_rate': 0}
    
    def _calculate_conversion_rate(self, affiliate_id: str = None,
                                  start_date: datetime = None, end_date: datetime = None) -> float:
        """コンバージョン率の計算"""
        try:
            clicks = self._get_clicks_from_db(affiliate_id, start_date, end_date)
            conversions = self._get_conversions_from_db(affiliate_id, start_date, end_date)
            
            total_clicks = len(clicks)
            total_conversions = len(conversions)
            
            return (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
            
        except Exception as e:
            self.logger.error(f"Conversion rate calculation failed: {e}")
            return 0.0
    
    def _get_top_performing_resources(self, conversions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """トップパフォーマンスリソースの取得"""
        try:
            resource_performance = {}
            
            for conversion in conversions:
                # クリック情報から resource_id を取得
                click_id = conversion.get('click_id')
                if click_id:
                    click_info = self._get_click_from_db(click_id)
                    if click_info:
                        resource_id = click_info.get('resource_id', 'unknown')
                        revenue = self._calculate_revenue_from_conversion(conversion)
                        
                        if resource_id not in resource_performance:
                            resource_performance[resource_id] = {
                                'resource_id': resource_id,
                                'conversions': 0,
                                'revenue': 0.0
                            }
                        
                        resource_performance[resource_id]['conversions'] += 1
                        resource_performance[resource_id]['revenue'] += revenue
            
            # 収益順でソート
            sorted_resources = sorted(
                resource_performance.values(),
                key=lambda x: x['revenue'],
                reverse=True
            )
            
            return sorted_resources[:10]  # トップ10
            
        except Exception as e:
            self.logger.error(f"Top performing resources calculation failed: {e}")
            return []
    
    def _calculate_trend(self, data: List[Dict[str, Any]], date_field: str) -> List[Dict[str, Any]]:
        """トレンド計算"""
        try:
            # 日別集計
            daily_counts = {}
            
            for item in data:
                date_str = item.get(date_field, '')
                if date_str:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    day_key = date_obj.strftime('%Y-%m-%d')
                    daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
            
            # 日付順でソート
            sorted_days = sorted(daily_counts.items())
            
            return [{'date': day, 'count': count} for day, count in sorted_days]
            
        except Exception as e:
            self.logger.error(f"Trend calculation failed: {e}")
            return []
    
    def _calculate_revenue_trend(self, conversions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """収益トレンド計算"""
        try:
            daily_revenue = {}
            
            for conversion in conversions:
                date_str = conversion.get('converted_at', '')
                if date_str:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    day_key = date_obj.strftime('%Y-%m-%d')
                    revenue = self._calculate_revenue_from_conversion(conversion)
                    daily_revenue[day_key] = daily_revenue.get(day_key, 0.0) + revenue
            
            # 日付順でソート
            sorted_days = sorted(daily_revenue.items())
            
            return [{'date': day, 'revenue': revenue} for day, revenue in sorted_days]
            
        except Exception as e:
            self.logger.error(f"Revenue trend calculation failed: {e}")
            return []
    
    # === 強化された追跡機能のヘルパーメソッド ===
    
    def _generate_secure_click_id(self, user_id: Optional[int], session_id: str, affiliate_id: str) -> str:
        """セキュアなクリックID生成"""
        try:
            # タイムスタンプ + ユーザー情報 + ランダム要素でハッシュ生成
            timestamp = str(int(time.time() * 1000))
            user_str = str(user_id) if user_id else session_id
            random_str = str(uuid.uuid4())
            
            hash_input = f"{timestamp}:{user_str}:{affiliate_id}:{random_str}"
            hash_object = hashlib.sha256(hash_input.encode())
            
            return hash_object.hexdigest()[:16]  # 16文字のハッシュ
            
        except Exception as e:
            self.logger.error(f"Secure click ID generation failed: {e}")
            return str(uuid.uuid4())
    
    def _calculate_fraud_score(self, user_id: Optional[int], session_id: str, 
                              request_info: Dict[str, Any]) -> float:
        """不正スコア計算"""
        try:
            fraud_score = 0.0
            
            # IPアドレスチェック
            ip_address = request_info.get('ip_address', '')
            if self._is_suspicious_ip(ip_address):
                fraud_score += 0.3
            
            # User-Agentチェック
            user_agent = request_info.get('user_agent', '')
            if self._is_suspicious_user_agent(user_agent):
                fraud_score += 0.2
            
            # クリック頻度チェック
            if self._has_high_click_frequency(user_id, session_id):
                fraud_score += 0.3
            
            # リファラーチェック
            referrer = request_info.get('referrer', '')
            if self._is_suspicious_referrer(referrer):
                fraud_score += 0.2
            
            return min(fraud_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Fraud score calculation failed: {e}")
            return 0.0
    
    def _is_duplicate_click(self, user_id: Optional[int], session_id: str, 
                           affiliate_id: str, resource_id: str, request_info: Dict[str, Any]) -> bool:
        """重複クリック検出"""
        try:
            # キャッシュキーの生成
            identifier = f"{user_id}:{session_id}" if user_id else session_id
            cache_key = f"recent_click:{identifier}:{affiliate_id}:{resource_id}"
            
            if self.cache:
                recent_click = self.cache.get(cache_key)
                if recent_click:
                    return True
                
                # 重複検出ウィンドウ内でキャッシュに記録
                self.cache.set(cache_key, True, ttl=self.duplicate_click_window)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Duplicate click detection failed: {e}")
            return False
    
    def _get_geo_info(self, ip_address: str) -> Dict[str, Any]:
        """地理的情報取得（簡易版）"""
        try:
            # 実際の実装では GeoIP データベースを使用
            # ここでは簡易的な実装
            if not ip_address or ip_address.startswith('127.') or ip_address.startswith('192.168.'):
                return {'country': 'Unknown', 'city': 'Unknown', 'is_local': True}
            
            # プライベートIPの判定
            private_ranges = ['10.', '172.16.', '192.168.']
            is_private = any(ip_address.startswith(range_) for range_ in private_ranges)
            
            return {
                'country': 'JP',  # デフォルト
                'city': 'Unknown',
                'is_private': is_private,
                'is_local': False
            }
            
        except Exception as e:
            self.logger.error(f"Geo info retrieval failed: {e}")
            return {'country': 'Unknown', 'city': 'Unknown', 'is_local': False}
    
    def _parse_device_info(self, user_agent: str) -> Dict[str, Any]:
        """デバイス情報解析"""
        try:
            if not user_agent:
                return {'device_type': 'Unknown', 'browser': 'Unknown', 'os': 'Unknown'}
            
            user_agent_lower = user_agent.lower()
            
            # デバイスタイプ判定
            if 'mobile' in user_agent_lower or 'android' in user_agent_lower:
                device_type = 'Mobile'
            elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
                device_type = 'Tablet'
            else:
                device_type = 'Desktop'
            
            # ブラウザ判定
            if 'chrome' in user_agent_lower:
                browser = 'Chrome'
            elif 'firefox' in user_agent_lower:
                browser = 'Firefox'
            elif 'safari' in user_agent_lower:
                browser = 'Safari'
            elif 'edge' in user_agent_lower:
                browser = 'Edge'
            else:
                browser = 'Other'
            
            # OS判定
            if 'windows' in user_agent_lower:
                os = 'Windows'
            elif 'mac' in user_agent_lower:
                os = 'macOS'
            elif 'linux' in user_agent_lower:
                os = 'Linux'
            elif 'android' in user_agent_lower:
                os = 'Android'
            elif 'ios' in user_agent_lower:
                os = 'iOS'
            else:
                os = 'Other'
            
            return {
                'device_type': device_type,
                'browser': browser,
                'os': os,
                'user_agent': user_agent
            }
            
        except Exception as e:
            self.logger.error(f"Device info parsing failed: {e}")
            return {'device_type': 'Unknown', 'browser': 'Unknown', 'os': 'Unknown'}
    
    def _calculate_click_quality_score(self, request_info: Dict[str, Any]) -> float:
        """クリック品質スコア計算"""
        try:
            quality_score = 0.5  # ベーススコア
            
            # リファラーの存在
            if request_info.get('referrer'):
                quality_score += 0.2
            
            # User-Agentの妥当性
            user_agent = request_info.get('user_agent', '')
            if user_agent and len(user_agent) > 50:  # 詳細なUser-Agent
                quality_score += 0.2
            
            # セッション情報の存在
            if request_info.get('session_duration', 0) > 30:  # 30秒以上のセッション
                quality_score += 0.1
            
            return min(quality_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Click quality score calculation failed: {e}")
            return 0.5
    
    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """疑わしいIPアドレスの判定"""
        try:
            if not ip_address:
                return True
            
            # 既知の不正IPリスト（実際の実装では外部データベースを使用）
            suspicious_ips = ['0.0.0.0', '127.0.0.1']
            
            return ip_address in suspicious_ips
            
        except Exception as e:
            self.logger.error(f"Suspicious IP check failed: {e}")
            return False
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """疑わしいUser-Agentの判定"""
        try:
            if not user_agent or len(user_agent) < 10:
                return True
            
            # 既知のボットUser-Agent
            bot_patterns = ['bot', 'crawler', 'spider', 'scraper']
            user_agent_lower = user_agent.lower()
            
            return any(pattern in user_agent_lower for pattern in bot_patterns)
            
        except Exception as e:
            self.logger.error(f"Suspicious user agent check failed: {e}")
            return False
    
    def _has_high_click_frequency(self, user_id: Optional[int], session_id: str) -> bool:
        """高頻度クリックの検出"""
        try:
            identifier = f"{user_id}:{session_id}" if user_id else session_id
            cache_key = f"click_frequency:{identifier}"
            
            if self.cache:
                click_count = self.cache.get(cache_key) or 0
                
                # 1分間に10回以上のクリックは疑わしい
                if click_count > 10:
                    return True
                
                # カウンターを増加
                self.cache.set(cache_key, click_count + 1, ttl=60)
            
            return False
            
        except Exception as e:
            self.logger.error(f"High click frequency check failed: {e}")
            return False
    
    def _is_suspicious_referrer(self, referrer: str) -> bool:
        """疑わしいリファラーの判定"""
        try:
            if not referrer:
                return False  # リファラーなしは必ずしも疑わしくない
            
            # 疑わしいドメインパターン
            suspicious_patterns = ['spam', 'fake', 'bot', 'test']
            referrer_lower = referrer.lower()
            
            return any(pattern in referrer_lower for pattern in suspicious_patterns)
            
        except Exception as e:
            self.logger.error(f"Suspicious referrer check failed: {e}")
            return False    # ==
= コンバージョン追跡強化機能 ===
    
    def _is_duplicate_conversion(self, click_id: str, conversion_type: ConversionType) -> bool:
        """重複コンバージョン検出"""
        try:
            if not self.db:
                return False
            
            sql = """
            SELECT COUNT(*) as count FROM affiliate_conversions 
            WHERE click_id = ? AND conversion_type = ?
            """
            
            if hasattr(self.db, 'fetch_one_with_retry'):
                result = self.db.fetch_one_with_retry(sql, (click_id, conversion_type.value))
            else:
                cursor = self.db.connection.execute(sql, (click_id, conversion_type.value))
                result = cursor.fetchone()
            
            return result and result.get('count', 0) > 0
            
        except Exception as e:
            self.logger.error(f"Duplicate conversion check failed: {e}")
            return False
    
    def _validate_conversion(self, click_info: Dict[str, Any], 
                           conversion_value: float, conversion_type: ConversionType) -> bool:
        """コンバージョン妥当性チェック"""
        try:
            # 値の妥当性チェック
            if conversion_value <= 0:
                return False
            
            # 異常に高い値のチェック
            if conversion_value > 1000000:  # 100万円以上は要確認
                self.logger.warning(f"Unusually high conversion value: {conversion_value}")
                return False
            
            # クリック品質スコアチェック
            click_metadata = click_info.get('metadata', {})
            fraud_score = click_metadata.get('fraud_score', 0)
            
            if fraud_score > 0.7:  # 高い不正スコア
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Conversion validation failed: {e}")
            return False
    
    def _calculate_attribution_weights(self, click_info: Dict[str, Any], 
                                     time_since_click: timedelta) -> Dict[str, float]:
        """アトリビューション重み計算"""
        try:
            weights = {}
            
            # ファーストクリック（常に1.0）
            weights['first_click'] = 1.0
            
            # ラストクリック（常に1.0）
            weights['last_click'] = 1.0
            
            # 線形アトリビューション（時間による減衰なし）
            weights['linear'] = 1.0
            
            # 時間減衰アトリビューション
            hours_since_click = time_since_click.total_seconds() / 3600
            decay_factor = max(0.1, 1.0 - (hours_since_click / (self.conversion_window_days * 24)))
            weights['time_decay'] = decay_factor
            
            return weights
            
        except Exception as e:
            self.logger.error(f"Attribution weights calculation failed: {e}")
            return {'first_click': 1.0, 'last_click': 1.0, 'linear': 1.0, 'time_decay': 1.0}
    
    def _calculate_conversion_quality_score(self, click_info: Dict[str, Any], 
                                          conversion_value: float, time_since_click: timedelta) -> float:
        """コンバージョン品質スコア計算"""
        try:
            quality_score = 0.5  # ベーススコア
            
            # クリック品質スコア
            click_metadata = click_info.get('metadata', {})
            click_quality = click_metadata.get('click_quality_score', 0.5)
            quality_score += click_quality * 0.3
            
            # コンバージョン時間の妥当性
            hours_since_click = time_since_click.total_seconds() / 3600
            if 1 <= hours_since_click <= 168:  # 1時間〜1週間が理想的
                quality_score += 0.2
            
            # コンバージョン値の妥当性
            if 100 <= conversion_value <= 50000:  # 適切な価格帯
                quality_score += 0.1
            
            return min(quality_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Conversion quality score calculation failed: {e}")
            return 0.5
    
    def _get_revenue_tier(self, affiliate_id: str) -> str:
        """収益ティアの取得"""
        try:
            # 過去30日の収益を計算
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=30)
            
            conversions = self._get_conversions_from_db(affiliate_id, start_date, end_date)
            total_revenue = sum(self._calculate_revenue_from_conversion(c) for c in conversions)
            
            # ティア判定
            for tier, config in reversed(list(self.revenue_sharing_tiers.items())):
                if total_revenue >= config['min_revenue']:
                    return tier
            
            return 'bronze'
            
        except Exception as e:
            self.logger.error(f"Revenue tier calculation failed: {e}")
            return 'bronze'
    
    def _get_conversion_path(self, user_id: Optional[int]) -> List[Dict[str, Any]]:
        """コンバージョンパスの取得"""
        try:
            if not user_id or not self.db:
                return []
            
            # 過去7日のクリック履歴を取得
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)
            
            sql = """
            SELECT affiliate_id, source, clicked_at, resource_id
            FROM affiliate_clicks 
            WHERE user_id = ? AND clicked_at >= ? AND clicked_at <= ?
            ORDER BY clicked_at ASC
            """
            
            if hasattr(self.db, 'fetch_all_with_retry'):
                clicks = self.db.fetch_all_with_retry(sql, (user_id, start_date, end_date))
            else:
                cursor = self.db.connection.execute(sql, (user_id, start_date, end_date))
                rows = cursor.fetchall()
                if rows:
                    columns = [description[0] for description in cursor.description]
                    clicks = [dict(zip(columns, row)) for row in rows]
                else:
                    clicks = []
            
            return clicks[-5:]  # 最新5件のクリック
            
        except Exception as e:
            self.logger.error(f"Conversion path retrieval failed: {e}")
            return []
    
    # === 収益計算強化機能 ===
    
    def calculate_enhanced_revenue(self, conversion: AffiliateConversion, 
                                 attribution_model: str = 'last_click') -> Dict[str, float]:
        """強化された収益計算"""
        try:
            base_revenue = self._calculate_revenue(conversion)
            
            # アトリビューション重みの適用
            attribution_weights = conversion.metadata.get('attribution_weights', {})
            attribution_weight = attribution_weights.get(attribution_model, 1.0)
            
            # 品質スコアによる調整
            quality_score = conversion.metadata.get('conversion_quality_score', 1.0)
            
            # ティアボーナスの適用
            revenue_tier = conversion.metadata.get('revenue_tier', 'bronze')
            tier_config = self.revenue_sharing_tiers.get(revenue_tier, {'bonus_rate': 0.0})
            bonus_rate = tier_config['bonus_rate']
            
            # 最終収益計算
            adjusted_revenue = base_revenue * attribution_weight * quality_score
            bonus_revenue = adjusted_revenue * bonus_rate
            total_revenue = adjusted_revenue + bonus_revenue
            
            return {
                'base_revenue': base_revenue,
                'attribution_weight': attribution_weight,
                'quality_adjustment': quality_score,
                'adjusted_revenue': adjusted_revenue,
                'tier_bonus': bonus_revenue,
                'total_revenue': total_revenue,
                'revenue_tier': revenue_tier
            }
            
        except Exception as e:
            self.logger.error(f"Enhanced revenue calculation failed: {e}")
            return {'total_revenue': self._calculate_revenue(conversion)}
    
    def get_advanced_analytics(self, affiliate_id: str = None, days: int = 30) -> Dict[str, Any]:
        """高度な分析データ"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            clicks = self._get_clicks_from_db(affiliate_id, start_date, end_date)
            conversions = self._get_conversions_from_db(affiliate_id, start_date, end_date)
            
            analytics = {
                'fraud_analysis': self._analyze_fraud_patterns(clicks),
                'quality_analysis': self._analyze_quality_patterns(clicks, conversions),
                'attribution_analysis': self._analyze_attribution_patterns(conversions),
                'device_analysis': self._analyze_device_patterns(clicks),
                'geographic_analysis': self._analyze_geographic_patterns(clicks),
                'temporal_analysis': self._analyze_temporal_patterns(clicks, conversions),
                'revenue_optimization': self._generate_revenue_optimization_recommendations(
                    clicks, conversions
                )
            }
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Advanced analytics generation failed: {e}")
            return {}
    
    def _analyze_fraud_patterns(self, clicks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """不正パターン分析"""
        try:
            total_clicks = len(clicks)
            if total_clicks == 0:
                return {}
            
            fraud_scores = []
            suspicious_ips = set()
            suspicious_user_agents = set()
            
            for click in clicks:
                metadata = json.loads(click.get('metadata', '{}'))
                fraud_score = metadata.get('fraud_score', 0)
                fraud_scores.append(fraud_score)
                
                if fraud_score > 0.7:
                    suspicious_ips.add(click.get('ip_address', ''))
                    suspicious_user_agents.add(click.get('user_agent', ''))
            
            return {
                'total_clicks': total_clicks,
                'average_fraud_score': sum(fraud_scores) / len(fraud_scores),
                'high_risk_clicks': len([s for s in fraud_scores if s > 0.7]),
                'suspicious_ips_count': len(suspicious_ips),
                'suspicious_user_agents_count': len(suspicious_user_agents),
                'fraud_rate': len([s for s in fraud_scores if s > 0.7]) / total_clicks * 100
            }
            
        except Exception as e:
            self.logger.error(f"Fraud pattern analysis failed: {e}")
            return {}
    
    def _analyze_quality_patterns(self, clicks: List[Dict[str, Any]], 
                                conversions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """品質パターン分析"""
        try:
            click_quality_scores = []
            conversion_quality_scores = []
            
            for click in clicks:
                metadata = json.loads(click.get('metadata', '{}'))
                quality_score = metadata.get('click_quality_score', 0.5)
                click_quality_scores.append(quality_score)
            
            for conversion in conversions:
                metadata = json.loads(conversion.get('metadata', '{}'))
                quality_score = metadata.get('conversion_quality_score', 0.5)
                conversion_quality_scores.append(quality_score)
            
            return {
                'average_click_quality': statistics.mean(click_quality_scores) if click_quality_scores else 0,
                'average_conversion_quality': statistics.mean(conversion_quality_scores) if conversion_quality_scores else 0,
                'high_quality_clicks': len([s for s in click_quality_scores if s > 0.8]),
                'high_quality_conversions': len([s for s in conversion_quality_scores if s > 0.8]),
                'quality_correlation': self._calculate_quality_correlation(
                    click_quality_scores, conversion_quality_scores
                )
            }
            
        except Exception as e:
            self.logger.error(f"Quality pattern analysis failed: {e}")
            return {}
    
    def _analyze_attribution_patterns(self, conversions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """アトリビューションパターン分析"""
        try:
            attribution_data = {}
            
            for model in self.conversion_attribution_models:
                attribution_data[model] = {
                    'total_revenue': 0.0,
                    'conversion_count': 0
                }
            
            for conversion in conversions:
                metadata = json.loads(conversion.get('metadata', '{}'))
                attribution_weights = metadata.get('attribution_weights', {})
                base_revenue = self._calculate_revenue_from_conversion(conversion)
                
                for model in self.conversion_attribution_models:
                    weight = attribution_weights.get(model, 1.0)
                    attributed_revenue = base_revenue * weight
                    
                    attribution_data[model]['total_revenue'] += attributed_revenue
                    attribution_data[model]['conversion_count'] += 1
            
            return attribution_data
            
        except Exception as e:
            self.logger.error(f"Attribution pattern analysis failed: {e}")
            return {}
    
    def _analyze_device_patterns(self, clicks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """デバイスパターン分析"""
        try:
            device_stats = {}
            
            for click in clicks:
                metadata = json.loads(click.get('metadata', '{}'))
                device_info = metadata.get('device_info', {})
                device_type = device_info.get('device_type', 'Unknown')
                
                if device_type not in device_stats:
                    device_stats[device_type] = {'clicks': 0, 'conversions': 0}
                
                device_stats[device_type]['clicks'] += 1
            
            return device_stats
            
        except Exception as e:
            self.logger.error(f"Device pattern analysis failed: {e}")
            return {}
    
    def _analyze_geographic_patterns(self, clicks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """地理的パターン分析"""
        try:
            geo_stats = {}
            
            for click in clicks:
                metadata = json.loads(click.get('metadata', '{}'))
                geo_info = metadata.get('geo_info', {})
                country = geo_info.get('country', 'Unknown')
                
                if country not in geo_stats:
                    geo_stats[country] = {'clicks': 0, 'conversions': 0}
                
                geo_stats[country]['clicks'] += 1
            
            return geo_stats
            
        except Exception as e:
            self.logger.error(f"Geographic pattern analysis failed: {e}")
            return {}
    
    def _analyze_temporal_patterns(self, clicks: List[Dict[str, Any]], 
                                 conversions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """時間パターン分析"""
        try:
            hourly_clicks = {}
            hourly_conversions = {}
            
            for click in clicks:
                clicked_at = datetime.fromisoformat(click['clicked_at'].replace('Z', '+00:00'))
                hour = clicked_at.hour
                hourly_clicks[hour] = hourly_clicks.get(hour, 0) + 1
            
            for conversion in conversions:
                converted_at = datetime.fromisoformat(conversion['converted_at'].replace('Z', '+00:00'))
                hour = converted_at.hour
                hourly_conversions[hour] = hourly_conversions.get(hour, 0) + 1
            
            return {
                'hourly_clicks': hourly_clicks,
                'hourly_conversions': hourly_conversions,
                'peak_click_hour': max(hourly_clicks.items(), key=lambda x: x[1])[0] if hourly_clicks else None,
                'peak_conversion_hour': max(hourly_conversions.items(), key=lambda x: x[1])[0] if hourly_conversions else None
            }
            
        except Exception as e:
            self.logger.error(f"Temporal pattern analysis failed: {e}")
            return {}
    
    def _generate_revenue_optimization_recommendations(self, clicks: List[Dict[str, Any]], 
                                                     conversions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """収益最適化推奨事項"""
        try:
            recommendations = []
            
            # 品質スコア分析
            quality_scores = []
            for click in clicks:
                metadata = json.loads(click.get('metadata', '{}'))
                quality_scores.append(metadata.get('click_quality_score', 0.5))
            
            if quality_scores and statistics.mean(quality_scores) < 0.6:
                recommendations.append({
                    'type': 'quality_improvement',
                    'priority': 'high',
                    'recommendation': 'クリック品質が低下しています。トラフィックソースの見直しを検討してください。'
                })
            
            # コンバージョン率分析
            conversion_rate = len(conversions) / len(clicks) * 100 if clicks else 0
            if conversion_rate < 2.0:  # 2%未満
                recommendations.append({
                    'type': 'conversion_optimization',
                    'priority': 'high',
                    'recommendation': 'コンバージョン率が低いです。ランディングページの最適化を検討してください。'
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Revenue optimization recommendations failed: {e}")
            return []
    
    def _calculate_quality_correlation(self, click_qualities: List[float], 
                                     conversion_qualities: List[float]) -> float:
        """品質相関の計算"""
        try:
            if len(click_qualities) < 2 or len(conversion_qualities) < 2:
                return 0.0
            
            # 簡単な相関係数計算
            mean_click = statistics.mean(click_qualities)
            mean_conversion = statistics.mean(conversion_qualities)
            
            numerator = sum((c - mean_click) * (v - mean_conversion) 
                          for c, v in zip(click_qualities, conversion_qualities))
            
            click_variance = sum((c - mean_click) ** 2 for c in click_qualities)
            conversion_variance = sum((v - mean_conversion) ** 2 for v in conversion_qualities)
            
            denominator = (click_variance * conversion_variance) ** 0.5
            
            return numerator / denominator if denominator > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"Quality correlation calculation failed: {e}")
            return 0.0    

    def _generate_secure_click_id(self, user_id: Optional[int], session_id: str, affiliate_id: str) -> str:
        """安全なクリックIDの生成"""
        try:
            # タイムスタンプ + ユーザー情報 + ランダム要素でハッシュ生成
            timestamp = str(int(time.time() * 1000))
            user_str = str(user_id) if user_id else 'anonymous'
            
            raw_string = f"{timestamp}_{user_str}_{session_id}_{affiliate_id}_{uuid.uuid4().hex[:8]}"
            
            # SHA256ハッシュ化
            hash_object = hashlib.sha256(raw_string.encode())
            click_id = hash_object.hexdigest()[:16]  # 16文字に短縮
            
            return f"tc_{click_id}"
            
        except Exception as e:
            self.logger.error(f"Secure click ID generation failed: {e}")
            return f"tc_{uuid.uuid4().hex[:16]}"
    
    def _calculate_fraud_score(self, user_id: Optional[int], session_id: str, request_info: Dict[str, Any]) -> float:
        """不正スコアの計算"""
        try:
            fraud_score = 0.0
            
            # IPアドレスチェック
            ip_address = request_info.get('ip_address', '')
            if ip_address.startswith('127.') or ip_address.startswith('10.') or ip_address.startswith('192.168.'):
                fraud_score += 0.3  # プライベートIPは疑わしい
            
            # ユーザーエージェントチェック
            user_agent = request_info.get('user_agent', '').lower()
            bot_indicators = ['bot', 'crawler', 'spider', 'scraper', 'automated']
            if any(indicator in user_agent for indicator in bot_indicators):
                fraud_score += 0.4
            
            # リファラーチェック
            referrer = request_info.get('referrer', '')
            if not referrer:
                fraud_score += 0.2  # リファラーなしは疑わしい
            
            # メタデータチェック
            metadata = request_info.get('metadata', {})
            if metadata.get('automated', False):
                fraud_score += 0.5
            
            return min(fraud_score, 1.0)  # 最大1.0にクリップ
            
        except Exception as e:
            self.logger.error(f"Fraud score calculation failed: {e}")
            return 0.0
    
    def _is_duplicate_click(self, user_id: Optional[int], session_id: str, 
                           affiliate_id: str, resource_id: str, request_info: Dict[str, Any]) -> bool:
        """重複クリックの検出"""
        try:
            # キャッシュキーの生成
            cache_key = f"recent_click:{user_id}:{session_id}:{affiliate_id}:{resource_id}"
            
            if self.cache:
                # 最近のクリックをチェック
                recent_click = self.cache.get(cache_key)
                if recent_click:
                    return True
                
                # 新しいクリックを記録（重複検出ウィンドウ分）
                self.cache.set(cache_key, True, ttl=self.duplicate_click_window)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Duplicate click detection failed: {e}")
            return False
    
    def _get_geo_info(self, ip_address: str) -> Dict[str, Any]:
        """地理的情報の取得（簡易実装）"""
        try:
            # 実際の実装では GeoIP データベースを使用
            if ip_address.startswith('203.104.'):
                return {'country': 'JP', 'region': 'Tokyo', 'city': 'Tokyo'}
            elif ip_address.startswith('192.168.') or ip_address.startswith('127.'):
                return {'country': 'LOCAL', 'region': 'Local', 'city': 'Local'}
            else:
                return {'country': 'UNKNOWN', 'region': 'Unknown', 'city': 'Unknown'}
                
        except Exception as e:
            self.logger.error(f"Geo info retrieval failed: {e}")
            return {'country': 'UNKNOWN', 'region': 'Unknown', 'city': 'Unknown'}
    
    def _parse_device_info(self, user_agent: str) -> Dict[str, Any]:
        """デバイス情報の解析"""
        try:
            device_info = {
                'device_type': 'unknown',
                'os': 'unknown',
                'browser': 'unknown',
                'is_mobile': False
            }
            
            user_agent_lower = user_agent.lower()
            
            # デバイスタイプの判定
            if 'mobile' in user_agent_lower or 'iphone' in user_agent_lower or 'android' in user_agent_lower:
                device_info['device_type'] = 'mobile'
                device_info['is_mobile'] = True
            elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
                device_info['device_type'] = 'tablet'
            else:
                device_info['device_type'] = 'desktop'
            
            # OS判定
            if 'windows' in user_agent_lower:
                device_info['os'] = 'windows'
            elif 'mac os' in user_agent_lower or 'macos' in user_agent_lower:
                device_info['os'] = 'macos'
            elif 'linux' in user_agent_lower:
                device_info['os'] = 'linux'
            elif 'android' in user_agent_lower:
                device_info['os'] = 'android'
            elif 'ios' in user_agent_lower or 'iphone' in user_agent_lower:
                device_info['os'] = 'ios'
            
            # ブラウザ判定
            if 'chrome' in user_agent_lower:
                device_info['browser'] = 'chrome'
            elif 'firefox' in user_agent_lower:
                device_info['browser'] = 'firefox'
            elif 'safari' in user_agent_lower:
                device_info['browser'] = 'safari'
            elif 'edge' in user_agent_lower:
                device_info['browser'] = 'edge'
            
            return device_info
            
        except Exception as e:
            self.logger.error(f"Device info parsing failed: {e}")
            return {'device_type': 'unknown', 'os': 'unknown', 'browser': 'unknown', 'is_mobile': False}
    
    def _calculate_click_quality_score(self, request_info: Dict[str, Any]) -> float:
        """クリック品質スコアの計算"""
        try:
            quality_score = 0.5  # ベーススコア
            
            # リファラーの品質
            referrer = request_info.get('referrer', '')
            if 'tou-connect.com' in referrer:
                quality_score += 0.2  # 自サイトからのリファラーは高品質
            elif referrer and not any(spam in referrer for spam in ['spam', 'bot', 'fake']):
                quality_score += 0.1
            
            # ユーザーエージェントの品質
            user_agent = request_info.get('user_agent', '')
            if user_agent and 'Mozilla' in user_agent and len(user_agent) > 50:
                quality_score += 0.1  # 正常なブラウザのユーザーエージェント
            
            # メタデータの品質
            metadata = request_info.get('metadata', {})
            if metadata.get('engagement_time', 0) > 30:  # 30秒以上の滞在
                quality_score += 0.1
            if metadata.get('page_views', 0) > 1:  # 複数ページ閲覧
                quality_score += 0.1
            if metadata.get('user_type') == 'registered':  # 登録ユーザー
                quality_score += 0.1
            
            return min(quality_score, 1.0)  # 最大1.0にクリップ
            
        except Exception as e:
            self.logger.error(f"Click quality score calculation failed: {e}")
            return 0.5
    
    def _is_duplicate_conversion(self, click_id: str, conversion_type: ConversionType) -> bool:
        """重複コンバージョンの検出"""
        try:
            if not self.db:
                return False
            
            # 同じクリックIDと同じコンバージョンタイプの組み合わせをチェック
            sql = "SELECT COUNT(*) FROM affiliate_conversions WHERE click_id = ? AND conversion_type = ?"
            
            if hasattr(self.db, 'fetch_one_with_retry'):
                result = self.db.fetch_one_with_retry(sql, (click_id, conversion_type.value))
            else:
                cursor = self.db.connection.execute(sql, (click_id, conversion_type.value))
                result = cursor.fetchone()
            
            count = result[0] if result else 0
            return count > 0
            
        except Exception as e:
            self.logger.error(f"Duplicate conversion detection failed: {e}")
            return False
    
    def _validate_conversion(self, click_info: Dict[str, Any], conversion_value: float, 
                           conversion_type: ConversionType) -> bool:
        """コンバージョンの妥当性チェック"""
        try:
            # 金額の妥当性チェック
            if conversion_value <= 0:
                return False
            
            # 異常に高い金額のチェック
            if conversion_value > 10000:  # $10,000以上は要確認
                self.logger.warning(f"High conversion value detected: {conversion_value}")
            
            # アフィリエイトパートナー別の妥当性チェック
            affiliate_id = click_info.get('affiliate_id', '')
            partner_config = self.affiliate_partners.get(affiliate_id, {})
            
            # パートナー固有の検証ロジック
            if affiliate_id == 'udemy' and conversion_value > 200:
                return False  # Udemyコースは通常$200以下
            elif affiliate_id == 'amazon' and conversion_value > 1000:
                return False  # Amazon商品は通常$1000以下
            
            return True
            
        except Exception as e:
            self.logger.error(f"Conversion validation failed: {e}")
            return True  # エラー時はデフォルトで有効とする
    
    def _calculate_attribution_weights(self, click_info: Dict[str, Any], time_since_click: timedelta) -> Dict[str, float]:
        """アトリビューション重みの計算"""
        try:
            weights = {}
            
            # ファーストクリック（最初のクリックに100%の重み）
            weights['first_click'] = 1.0
            
            # ラストクリック（最後のクリックに100%の重み）
            weights['last_click'] = 1.0
            
            # 線形減衰（時間に応じて線形に減衰）
            hours_since_click = time_since_click.total_seconds() / 3600
            max_hours = self.conversion_window_days * 24
            weights['linear'] = max(0, 1 - (hours_since_click / max_hours))
            
            # 時間減衰（指数関数的に減衰）
            decay_rate = 0.1  # 減衰率
            weights['time_decay'] = math.exp(-decay_rate * hours_since_click / 24)
            
            return weights
            
        except Exception as e:
            self.logger.error(f"Attribution weights calculation failed: {e}")
            return {'first_click': 1.0, 'last_click': 1.0, 'linear': 1.0, 'time_decay': 1.0}
    
    def _calculate_conversion_quality_score(self, click_info: Dict[str, Any], 
                                          conversion_value: float, time_since_click: timedelta) -> float:
        """コンバージョン品質スコアの計算"""
        try:
            quality_score = 0.5  # ベーススコア
            
            # クリック品質の影響
            click_metadata = json.loads(click_info.get('metadata', '{}'))
            click_quality = click_metadata.get('click_quality_score', 0.5)
            quality_score += click_quality * 0.3
            
            # コンバージョン速度の影響
            hours_since_click = time_since_click.total_seconds() / 3600
            if hours_since_click < 1:  # 1時間以内
                quality_score += 0.2  # 高速コンバージョンは高品質
            elif hours_since_click > 24 * 7:  # 1週間以上
                quality_score -= 0.1  # 遅いコンバージョンは品質が低い可能性
            
            # 金額の妥当性
            if 10 <= conversion_value <= 500:  # 適切な価格帯
                quality_score += 0.1
            
            return min(max(quality_score, 0.0), 1.0)  # 0-1の範囲にクリップ
            
        except Exception as e:
            self.logger.error(f"Conversion quality score calculation failed: {e}")
            return 0.5
    
    def _get_revenue_tier(self, affiliate_id: str) -> str:
        """収益ティアの取得"""
        try:
            # 過去30日間の収益を取得
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=30)
            
            conversions = self._get_conversions_from_db(affiliate_id, start_date, end_date)
            total_revenue = sum(self._calculate_revenue_from_conversion(c) for c in conversions)
            
            # ティア判定
            for tier, config in reversed(list(self.revenue_sharing_tiers.items())):
                if total_revenue >= config['min_revenue']:
                    return tier
            
            return 'bronze'  # デフォルト
            
        except Exception as e:
            self.logger.error(f"Revenue tier calculation failed: {e}")
            return 'bronze'
    
    def _get_conversion_path(self, user_id: Optional[int]) -> List[str]:
        """コンバージョンパスの取得"""
        try:
            if not user_id or not self.db:
                return []
            
            # ユーザーの過去のクリック履歴を取得
            sql = """
                SELECT source, clicked_at 
                FROM affiliate_clicks 
                WHERE user_id = ? 
                ORDER BY clicked_at DESC 
                LIMIT 10
            """
            
            if hasattr(self.db, 'fetch_all_with_retry'):
                clicks = self.db.fetch_all_with_retry(sql, (user_id,))
            else:
                cursor = self.db.connection.execute(sql, (user_id,))
                clicks = cursor.fetchall()
            
            # ソースのリストを返す
            return [click[0] for click in clicks] if clicks else []
            
        except Exception as e:
            self.logger.error(f"Conversion path retrieval failed: {e}")
            return []
    
    def _calculate_trend(self, data_list: List[Dict], date_field: str) -> Dict[str, Any]:
        """トレンドの計算"""
        try:
            if not data_list:
                return {'direction': 'stable', 'change_rate': 0}
            
            # 日別データの集計
            daily_counts = {}
            for item in data_list:
                date_str = item[date_field][:10]  # YYYY-MM-DD
                daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
            
            # 時系列データの作成
            sorted_dates = sorted(daily_counts.keys())
            if len(sorted_dates) < 2:
                return {'direction': 'stable', 'change_rate': 0}
            
            values = [daily_counts[date] for date in sorted_dates]
            
            # 線形回帰による傾向分析
            n = len(values)
            x = list(range(n))
            
            sum_x = sum(x)
            sum_y = sum(values)
            sum_xy = sum(x[i] * values[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            
            # 変化率の計算
            avg_value = sum_y / n
            change_rate = (slope / avg_value * 100) if avg_value > 0 else 0
            
            # 方向の判定
            if slope > 0.1:
                direction = 'increasing'
            elif slope < -0.1:
                direction = 'decreasing'
            else:
                direction = 'stable'
            
            return {
                'direction': direction,
                'change_rate': round(change_rate, 2),
                'slope': slope
            }
            
        except Exception as e:
            self.logger.error(f"Trend calculation failed: {e}")
            return {'direction': 'stable', 'change_rate': 0}
    
    def _calculate_revenue_trend(self, conversions: List[Dict]) -> Dict[str, Any]:
        """収益トレンドの計算"""
        try:
            if not conversions:
                return {'direction': 'stable', 'change_rate': 0}
            
            # 日別収益の集計
            daily_revenue = {}
            for conversion in conversions:
                date_str = conversion['converted_at'][:10]  # YYYY-MM-DD
                revenue = self._calculate_revenue_from_conversion(conversion)
                daily_revenue[date_str] = daily_revenue.get(date_str, 0) + revenue
            
            # トレンド計算
            sorted_dates = sorted(daily_revenue.keys())
            if len(sorted_dates) < 2:
                return {'direction': 'stable', 'change_rate': 0}
            
            values = [daily_revenue[date] for date in sorted_dates]
            
            # 変化率の計算
            if len(values) >= 2:
                start_value = values[0]
                end_value = values[-1]
                change_rate = ((end_value - start_value) / start_value * 100) if start_value > 0 else 0
                
                if change_rate > 5:
                    direction = 'increasing'
                elif change_rate < -5:
                    direction = 'decreasing'
                else:
                    direction = 'stable'
            else:
                direction = 'stable'
                change_rate = 0
            
            return {
                'direction': direction,
                'change_rate': round(change_rate, 2),
                'daily_values': values
            }
            
        except Exception as e:
            self.logger.error(f"Revenue trend calculation failed: {e}")
            return {'direction': 'stable', 'change_rate': 0}