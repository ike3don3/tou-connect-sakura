import os
import time
import logging
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

# セキュリティ・設定関連のインポート
from security.security_manager import init_security
from config.production_config import get_config

# データベース関連のインポート
from database.database_manager import DatabaseManager
from database.production_database_manager import ProductionDatabaseManager
from database.schema_manager import SchemaManager
from repositories.user_repository import UserRepository
from repositories.analysis_repository import AnalysisRepository
from repositories.interests_skills_repository import InterestsSkillsRepository
from matching.matching_engine import MatchingEngine
from learning_resources.resource_recommender import LearningResourceRecommender
from privacy.privacy_manager import PrivacyManager
from infrastructure.health_check_manager import HealthCheckManager
from infrastructure.logging_manager import logging_manager, request_context, log_user_action, log_security_event

# 監視・運用システムのインポート
from monitoring.monitoring_manager import MonitoringManager, AlertSeverity, MetricType
from monitoring.metrics_collector import MetricsCollector
from monitoring.alert_manager import AlertManager
from monitoring.metrics_visualizer import MetricsVisualizer

# キャッシュシステムのインポート
from cache.cache_factory import get_cache_factory, get_cache_manager, get_user_data_cache, get_analysis_cache, is_cache_available

# 最適化システムのインポート
from optimization.static_optimizer import StaticOptimizer

# 収益化システムのインポート
from revenue.affiliate_tracker import AffiliateTracker, ClickSource, ConversionType
from revenue.revenue_dashboard import RevenueDashboard

# 環境変数読み込み（開発環境のみ）
if os.getenv('ENVIRONMENT', 'development') == 'development':
    load_dotenv()

def create_app(environment=None):
    """アプリケーションファクトリ"""
    app = Flask(__name__)
    
    # 設定の読み込み
    config = get_config(environment)
    app.config.from_object(config)
    
    # ログ設定
    setup_logging(app)
    
    # セキュリティマネージャーの初期化
    security_manager = init_security(app)
    
    # Gemini API設定（テスト環境では省略可能）
    if not app.config.get('TESTING', False):
        api_key = security_manager.get_api_key('gemini')
        if not api_key:
            raise ValueError("GEMINI_API_KEY が設定されていません")
        genai.configure(api_key=api_key)
    else:
        # テスト環境用のダミー設定
        genai.configure(api_key='test-api-key')
    
    # データベース初期化
    db_url = app.config.get('DATABASE_URL', 'sqlite:///tou_connect.db')
    
    # 本番環境ではProductionDatabaseManagerを使用
    if environment == 'production' or (db_url.startswith('postgresql') or db_url.startswith('mysql')):
        db = ProductionDatabaseManager(db_url)
        
        # スキーマ管理
        schema_manager = SchemaManager(db)
        try:
            schema_manager.create_production_schema()
        except Exception as e:
            app.logger.warning(f"Schema creation warning: {e}")
    else:
        # 開発・テスト環境では従来のDatabaseManagerを使用
        if db_url.startswith('sqlite'):
            db_path = db_url.replace('sqlite:///', '')
            db = DatabaseManager(db_path)
        else:
            db = DatabaseManager(db_url)
    
    # 監視・運用システムの初期化
    monitoring_manager = MonitoringManager(db)
    metrics_collector = MetricsCollector(monitoring_manager, db)
    alert_manager = AlertManager(monitoring_manager, db)
    metrics_visualizer = MetricsVisualizer(monitoring_manager)
    
    # キャッシュシステムの初期化
    cache_factory = get_cache_factory()
    cache_manager = cache_factory.cache_manager
    user_data_cache = cache_factory.user_data_cache
    analysis_cache = cache_factory.analysis_cache
    
    # キャッシュシステムのヘルスチェック
    if is_cache_available():
        app.logger.info("Cache system initialized successfully")
    else:
        app.logger.warning("Cache system not available, running without cache")
    
    # 静的ファイル最適化システムの初期化
    optimization_config = {
        'enabled': app.config.get('OPTIMIZATION_ENABLED', True),
        'output_dir': app.config.get('OPTIMIZATION_OUTPUT_DIR', 'static/optimized'),
        'cdn': {
            'enabled': app.config.get('CDN_ENABLED', False),
            'base_url': app.config.get('CDN_BASE_URL', ''),
            'domains': app.config.get('CDN_DOMAINS', '').split(',') if app.config.get('CDN_DOMAINS') else []
        }
    }
    static_optimizer = StaticOptimizer(optimization_config, monitoring_manager)
    
    # 収益化システムの初期化
    affiliate_tracker = AffiliateTracker(db, cache_manager, monitoring_manager)
    revenue_dashboard = RevenueDashboard(affiliate_tracker, db, monitoring_manager)
    
    # メトリクス収集開始
    if not app.config.get('TESTING', False):
        metrics_collector.start_collection()
        app.logger.info("Metrics collection started")
        
        # キャッシュウォームアップ（新しいファクトリーシステムを使用）
        if cache_manager and user_data_cache and analysis_cache:
            app.logger.info("Cache warm-up completed")
    
    # リポジトリの初期化
    user_repo = UserRepository(db)
    analysis_repo = AnalysisRepository(db)
    interests_skills_repo = InterestsSkillsRepository(db)
    matching_engine = MatchingEngine(db)
    resource_recommender = LearningResourceRecommender(db)
    privacy_manager = PrivacyManager(db)
    health_check_manager = HealthCheckManager(db, security_manager)
    
    # ルートの登録
    register_routes(app, security_manager, user_repo, analysis_repo, 
                   interests_skills_repo, matching_engine, resource_recommender, 
                   privacy_manager, health_check_manager, monitoring_manager, 
                   metrics_collector, alert_manager, metrics_visualizer, 
                   cache_manager, user_data_cache, analysis_cache, static_optimizer,
                   affiliate_tracker, revenue_dashboard)
    
    # エラーハンドラーの登録
    register_error_handlers(app, security_manager)
    
    # アプリケーション終了時のクリーンアップ
    @app.teardown_appcontext
    def cleanup_monitoring(error):
        """アプリケーション終了時のクリーンアップ"""
        if error:
            # エラー発生時のメトリクス記録
            monitoring_manager.record_counter(
                "application.errors.total",
                1,
                {'error_type': type(error).__name__}
            )
    
    # アプリケーション終了時の処理
    import atexit
    
    def shutdown_monitoring():
        """監視システムのシャットダウン"""
        try:
            metrics_collector.stop_collection()
            monitoring_manager.stop_background_tasks()
            app.logger.info("Monitoring system shutdown completed")
        except Exception as e:
            app.logger.error(f"Monitoring shutdown error: {e}")
    
    atexit.register(shutdown_monitoring)
    
    return app

def setup_logging(app):
    """ログ設定"""
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    log_format = app.config.get('LOG_FORMAT', '%(asctime)s %(levelname)s %(name)s: %(message)s')
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/app.log') if os.path.exists('logs') else logging.StreamHandler()
        ]
    )
    
    # Werkzeugのログレベルを調整
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

def register_routes(app, security_manager, user_repo, analysis_repo, 
                   interests_skills_repo, matching_engine, resource_recommender, 
                   privacy_manager, health_check_manager, monitoring_manager, 
                   metrics_collector, alert_manager, metrics_visualizer,
                   cache_manager, cache_strategies, static_optimizer):
    """ルートの登録"""
    
    @app.before_request
    def before_request():
        """リクエスト前処理"""
        import uuid
        import time
        
        # リクエストIDの生成
        request_id = str(uuid.uuid4())
        request.start_time = time.time()
        
        # リクエストコンテキストの設定
        request_context.set_request_context(
            request_id=request_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            user_id=None  # 認証システム実装時に設定
        )
        
        # セキュリティログ
        if request.endpoint not in ['health_check', 'readiness_check', 'liveness_check']:
            log_security_event(
                'request_received',
                'low',
                {
                    'method': request.method,
                    'path': request.path,
                    'endpoint': request.endpoint
                }
            )
    
    @app.after_request
    def after_request(response):
        """リクエスト後処理"""
        import time
        
        if hasattr(request, 'start_time'):
            response_time = (time.time() - request.start_time) * 1000
            
            # APIリクエストログ
            logger = logging_manager.get_logger('api_requests')
            logging_manager.log_api_request(
                logger,
                request.method,
                request.path,
                response.status_code,
                response_time,
                request_context.get_context()
            )
            
            # 監視システムにパフォーマンスメトリクスを記録
            endpoint = request.endpoint or 'unknown'
            success = response.status_code < 400
            
            monitoring_manager.track_performance(
                f"api_{endpoint}",
                response_time,
                success,
                {
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'user_agent': request.headers.get('User-Agent', '')[:100]
                }
            )
            
            # レスポンス時間メトリクス
            monitoring_manager.record_timer(
                "http.request.duration",
                response_time,
                {
                    'method': request.method,
                    'endpoint': endpoint,
                    'status_code': str(response.status_code)
                }
            )
            
            # HTTPステータスカウンター
            monitoring_manager.record_counter(
                "http.requests.total",
                1,
                {
                    'method': request.method,
                    'endpoint': endpoint,
                    'status_code': str(response.status_code)
                }
            )
        
        # 静的ファイルのキャッシュヘッダー設定
        if request.path.startswith('/static/'):
            asset_type = static_optimizer.cdn_manager._detect_asset_type(request.path)
            cache_headers = static_optimizer.cdn_manager.get_cache_headers(asset_type)
            
            for header_name, header_value in cache_headers.items():
                response.headers[header_name] = header_value
            
            # 圧縮ヘッダーの設定
            if request.headers.get('Accept-Encoding', '').find('gzip') != -1:
                response.headers['Vary'] = 'Accept-Encoding'
        
        # セキュリティヘッダーの適用
        response = security_manager.apply_security_headers(response)
        
        return response

    @app.route('/')
    def index():
        """メインページ"""
        return render_template('index.html')

    @app.route('/matching')
    def matching():
        """学友マッチングページ"""
        return render_template('matching.html')

    @app.route('/resources')
    def resources():
        """学習リソースページ"""
        return render_template('resources.html')

    @app.route('/privacy')
    def privacy_policy():
        """プライバシーポリシーページ"""
        return render_template('privacy.html')

    @app.route('/terms')
    def terms_of_service():
        """利用規約ページ"""
        return render_template('terms.html')

    @app.route('/monitoring')
    def monitoring_dashboard():
        """監視ダッシュボードページ"""
        return render_template('monitoring_dashboard.html')

    @app.route('/api/consent', methods=['POST'])
    def create_consent():
        """ユーザー同意の記録"""
        if not app.config.get('TESTING', False):
            if not security_manager.validate_request(request):
                return security_manager.create_error_response(400, "Invalid request")
        
        try:
            data = request.get_json()
            
            # ユーザーIDの取得（セッションまたはリクエストから）
            # 実装では適切な認証システムと連携
            user_id = data.get('user_id') or 1  # テスト用
            
            # 各種同意の記録
            success = True
            if data.get('privacy_policy'):
                success &= privacy_manager.create_consent_record(
                    user_id, 'privacy_policy', metadata=data
                )
            
            if data.get('terms_of_service'):
                success &= privacy_manager.create_consent_record(
                    user_id, 'terms_of_service', metadata=data
                )
            
            if data.get('ai_analysis'):
                success &= privacy_manager.create_consent_record(
                    user_id, 'ai_analysis', metadata=data
                )
            
            if success:
                return jsonify({'success': True, 'message': '同意が記録されました'})
            else:
                return jsonify({'success': False, 'message': '同意の記録に失敗しました'}), 500
                
        except Exception as e:
            app.logger.error(f"Consent creation error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'サーバーエラーが発生しました')

    @app.route('/api/consent/status')
    def consent_status():
        """ユーザーの同意状況確認"""
        try:
            # ユーザーIDの取得（実装では適切な認証システムと連携）
            user_id = request.args.get('user_id', 1, type=int)  # テスト用
            
            consent_check = privacy_manager.check_consent_required(user_id)
            
            return jsonify({
                'consent_required': consent_check['any_required'],
                'privacy_policy_required': consent_check['privacy_policy_required'],
                'terms_required': consent_check['terms_required']
            })
            
        except Exception as e:
            app.logger.error(f"Consent status error: {e}", exc_info=True)
            return jsonify({'consent_required': True})  # 安全側に倒す

    @app.route('/api/user/data/export')
    def export_user_data():
        """ユーザーデータのエクスポート（GDPR準拠）"""
        try:
            # ユーザーIDの取得（実装では適切な認証システムと連携）
            user_id = request.args.get('user_id', type=int)
            if not user_id:
                return security_manager.create_error_response(400, 'ユーザーIDが必要です')
            
            export_data = privacy_manager.export_user_data(user_id)
            
            if 'error' in export_data:
                return security_manager.create_error_response(500, export_data['error'])
            
            return jsonify(export_data)
            
        except Exception as e:
            app.logger.error(f"Data export error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'データエクスポートに失敗しました')

    @app.route('/api/user/data/delete', methods=['POST'])
    def delete_user_data():
        """ユーザーデータの削除（GDPR準拠）"""
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            deletion_type = data.get('deletion_type', 'complete')  # complete or anonymize
            
            if not user_id:
                return security_manager.create_error_response(400, 'ユーザーIDが必要です')
            
            success = privacy_manager.delete_user_data(user_id, deletion_type)
            
            if success:
                return jsonify({
                    'success': True, 
                    'message': f'データ{deletion_type}が完了しました'
                })
            else:
                return jsonify({
                    'success': False, 
                    'message': 'データ削除に失敗しました'
                }), 500
                
        except Exception as e:
            app.logger.error(f"Data deletion error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'データ削除に失敗しました')

    # データベース参照をクロージャで保持
    app_db = db
    app_schema_manager = schema_manager if 'schema_manager' in locals() else None
    
    @app.route('/api/admin/database/stats')
    def database_stats():
        """データベース統計情報（管理者用）"""
        try:
            if isinstance(app_db, ProductionDatabaseManager):
                stats = app_db.get_database_stats()
                return jsonify(stats)
            else:
                # 基本的な統計情報
                return jsonify({
                    'database_type': 'sqlite',
                    'connection_pool': {'enabled': False},
                    'message': 'Limited stats available for SQLite'
                })
                
        except Exception as e:
            app.logger.error(f"Database stats error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'データベース統計取得に失敗しました')

    @app.route('/api/admin/database/backup', methods=['POST'])
    def create_database_backup():
        """データベースバックアップ作成（管理者用）"""
        try:
            if not isinstance(app_db, ProductionDatabaseManager):
                return security_manager.create_error_response(400, 'バックアップ機能は本番環境でのみ利用可能です')
            
            data = request.get_json() or {}
            backup_type = data.get('backup_type', 'full')
            
            backup_id = app_db.create_backup(backup_type)
            
            return jsonify({
                'success': True,
                'backup_id': backup_id,
                'backup_type': backup_type,
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            app.logger.error(f"Database backup error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'バックアップ作成に失敗しました')

    @app.route('/api/admin/database/backups')
    def list_database_backups():
        """データベースバックアップ一覧（管理者用）"""
        try:
            if not isinstance(app_db, ProductionDatabaseManager):
                return security_manager.create_error_response(400, 'バックアップ機能は本番環境でのみ利用可能です')
            
            backups = app_db.backup_manager.list_backups()
            
            return jsonify({
                'backups': backups,
                'total_backups': len(backups)
            })
            
        except Exception as e:
            app.logger.error(f"Backup list error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'バックアップ一覧取得に失敗しました')

    @app.route('/api/admin/database/schema')
    def database_schema_info():
        """データベーススキーマ情報（管理者用）"""
        try:
            if app_schema_manager:
                schema_info = app_schema_manager.get_schema_info()
                return jsonify(schema_info)
            else:
                return jsonify({
                    'message': 'Schema manager not available',
                    'database_type': getattr(app_db, 'db_type', 'sqlite')
                })
                
        except Exception as e:
            app.logger.error(f"Schema info error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'スキーマ情報取得に失敗しました')

    @app.route('/health')
    def health_check():
        """包括的ヘルスチェックエンドポイント"""
        try:
            health_status = health_check_manager.get_comprehensive_health_status()
            
            # ステータスコードの決定
            if health_status['status'] == 'healthy':
                status_code = 200
            elif health_status['status'] == 'degraded':
                status_code = 200  # 部分的に動作している
            else:
                status_code = 503  # サービス利用不可
            
            return jsonify(health_status), status_code
            
        except Exception as e:
            app.logger.error(f"Health check failed: {e}", exc_info=True)
            return jsonify({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 503

    @app.route('/health/ready')
    def readiness_check():
        """Readiness probe（Kubernetes対応）"""
        try:
            readiness_status = health_check_manager.get_readiness_status()
            status_code = 200 if readiness_status['status'] == 'ready' else 503
            return jsonify(readiness_status), status_code
        except Exception as e:
            return jsonify({
                "status": "not_ready",
                "error": str(e)
            }), 503

    @app.route('/health/live')
    def liveness_check():
        """Liveness probe（Kubernetes対応）"""
        try:
            liveness_status = health_check_manager.get_liveness_status()
            status_code = 200 if liveness_status['status'] == 'alive' else 503
            return jsonify(liveness_status), status_code
        except Exception as e:
            return jsonify({
                "status": "dead",
                "error": str(e)
            }), 503

    # 監視・運用システムのAPIエンドポイント
    @app.route('/api/monitoring/metrics')
    def get_metrics():
        """メトリクス取得API"""
        try:
            hours = request.args.get('hours', 24, type=int)
            name_pattern = request.args.get('name_pattern')
            
            metrics = monitoring_manager.get_metrics(name_pattern, hours)
            
            return jsonify({
                'metrics': metrics,
                'total_count': len(metrics),
                'hours': hours,
                'name_pattern': name_pattern
            })
            
        except Exception as e:
            app.logger.error(f"Metrics API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'メトリクス取得に失敗しました')

    @app.route('/api/monitoring/alerts')
    def get_alerts():
        """アラート取得API"""
        try:
            hours = request.args.get('hours', 24, type=int)
            severity = request.args.get('severity')
            active_only = request.args.get('active_only', 'false').lower() == 'true'
            
            # 重要度フィルタ
            severity_filter = None
            if severity:
                try:
                    severity_filter = AlertSeverity(severity.lower())
                except ValueError:
                    pass
            
            alerts = monitoring_manager.get_alerts(severity_filter, active_only, hours)
            
            return jsonify({
                'alerts': alerts,
                'total_count': len(alerts),
                'active_count': len([a for a in alerts if not a['resolved']]),
                'hours': hours,
                'severity_filter': severity,
                'active_only': active_only
            })
            
        except Exception as e:
            app.logger.error(f"Alerts API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'アラート取得に失敗しました')

    @app.route('/api/monitoring/alerts/<alert_id>/resolve', methods=['POST'])
    def resolve_alert(alert_id):
        """アラート解決API"""
        try:
            data = request.get_json() or {}
            resolution_note = data.get('resolution_note', '')
            
            monitoring_manager.resolve_alert(alert_id, resolution_note)
            
            return jsonify({
                'success': True,
                'alert_id': alert_id,
                'resolution_note': resolution_note,
                'resolved_at': datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            app.logger.error(f"Alert resolution error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'アラート解決に失敗しました')

    @app.route('/api/monitoring/performance')
    def get_performance_stats():
        """パフォーマンス統計API"""
        try:
            hours = request.args.get('hours', 24, type=int)
            operation = request.args.get('operation')
            
            perf_stats = monitoring_manager.get_performance_stats(operation, hours)
            
            return jsonify({
                'performance_stats': perf_stats,
                'operation_filter': operation,
                'hours': hours,
                'operations_count': len(perf_stats)
            })
            
        except Exception as e:
            app.logger.error(f"Performance stats API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'パフォーマンス統計取得に失敗しました')

    @app.route('/api/monitoring/overview')
    def get_monitoring_overview():
        """監視システム概要API"""
        try:
            system_overview = monitoring_manager.get_system_overview()
            metrics_summary = metrics_collector.get_metrics_summary()
            
            return jsonify({
                'system_overview': system_overview,
                'metrics_collection': metrics_summary,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            app.logger.error(f"Monitoring overview API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, '監視概要取得に失敗しました')

    @app.route('/api/monitoring/alerts', methods=['POST'])
    def create_manual_alert():
        """手動アラート作成API（管理者用）"""
        try:
            data = request.get_json()
            
            severity_str = data.get('severity', 'medium').lower()
            try:
                severity = AlertSeverity(severity_str)
            except ValueError:
                severity = AlertSeverity.MEDIUM
            
            title = data.get('title', 'Manual Alert')
            message = data.get('message', '')
            source = data.get('source', 'manual')
            metadata = data.get('metadata', {})
            
            alert_id = monitoring_manager.create_alert(
                severity, title, message, source, metadata
            )
            
            return jsonify({
                'success': True,
                'alert_id': alert_id,
                'severity': severity.value,
                'title': title,
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            app.logger.error(f"Manual alert creation error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'アラート作成に失敗しました')

    @app.route('/api/monitoring/metrics/custom', methods=['POST'])
    def record_custom_metric():
        """カスタムメトリクス記録API"""
        try:
            data = request.get_json()
            
            name = data.get('name')
            value = data.get('value')
            metric_type_str = data.get('type', 'gauge').lower()
            tags = data.get('tags', {})
            unit = data.get('unit', '')
            
            if not name or value is None:
                return security_manager.create_error_response(400, 'nameとvalueは必須です')
            
            # メトリクスタイプの変換
            try:
                metric_type = MetricType(metric_type_str)
            except ValueError:
                metric_type = MetricType.GAUGE
            
            monitoring_manager.record_metric(name, float(value), metric_type, tags, unit)
            
            return jsonify({
                'success': True,
                'name': name,
                'value': value,
                'type': metric_type.value,
                'tags': tags,
                'unit': unit,
                'recorded_at': datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            app.logger.error(f"Custom metric recording error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'メトリクス記録に失敗しました')

    # アラート管理API
    @app.route('/api/monitoring/alert-rules')
    def get_alert_rules():
        """アラートルール一覧API"""
        try:
            rules = alert_manager.get_alert_rules()
            return jsonify(rules)
        except Exception as e:
            app.logger.error(f"Alert rules API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'アラートルール取得に失敗しました')

    @app.route('/api/monitoring/alert-rules', methods=['POST'])
    def add_alert_rule():
        """アラートルール追加API"""
        try:
            from monitoring.alert_manager import ThresholdRule
            
            data = request.get_json()
            
            rule = ThresholdRule(
                metric_name=data['metric_name'],
                operator=data['operator'],
                threshold_value=float(data['threshold_value']),
                duration_minutes=int(data.get('duration_minutes', 5)),
                severity=AlertSeverity(data.get('severity', 'medium')),
                description=data.get('description', '')
            )
            
            rule_id = alert_manager.add_threshold_rule(rule)
            
            return jsonify({
                'success': True,
                'rule_id': rule_id,
                'message': 'アラートルールが追加されました'
            })
            
        except Exception as e:
            app.logger.error(f"Add alert rule error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'アラートルール追加に失敗しました')

    @app.route('/api/monitoring/alert-rules/<rule_id>', methods=['DELETE'])
    def delete_alert_rule(rule_id):
        """アラートルール削除API"""
        try:
            success = alert_manager.remove_threshold_rule(rule_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'アラートルールが削除されました'
                })
            else:
                return security_manager.create_error_response(404, 'アラートルールが見つかりません')
                
        except Exception as e:
            app.logger.error(f"Delete alert rule error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'アラートルール削除に失敗しました')

    @app.route('/api/monitoring/notifications/channels')
    def get_notification_channels():
        """通知チャネル一覧API"""
        try:
            channels = alert_manager.get_notification_channels()
            return jsonify(channels)
        except Exception as e:
            app.logger.error(f"Notification channels API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, '通知チャネル取得に失敗しました')

    @app.route('/api/monitoring/notifications/test/<channel_name>', methods=['POST'])
    def test_notification_channel(channel_name):
        """通知チャネルテストAPI"""
        try:
            success = alert_manager.test_notification_channel(channel_name)
            
            return jsonify({
                'success': success,
                'message': 'テスト通知が送信されました' if success else 'テスト通知の送信に失敗しました'
            })
            
        except Exception as e:
            app.logger.error(f"Test notification error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'テスト通知に失敗しました')

    @app.route('/api/monitoring/alert-statistics')
    def get_alert_statistics():
        """アラート統計API"""
        try:
            stats = alert_manager.get_alert_statistics()
            return jsonify(stats)
        except Exception as e:
            app.logger.error(f"Alert statistics API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'アラート統計取得に失敗しました')

    # メトリクス可視化API
    @app.route('/api/monitoring/visualize/timeseries')
    def get_timeseries_data():
        """時系列データAPI"""
        try:
            metric_names = request.args.getlist('metrics')
            hours = request.args.get('hours', 24, type=int)
            interval = request.args.get('interval', '5m')
            
            if not metric_names:
                return security_manager.create_error_response(400, 'メトリクス名が必要です')
            
            data = metrics_visualizer.get_time_series_data(metric_names, hours, interval)
            return jsonify(data)
            
        except Exception as e:
            app.logger.error(f"Timeseries API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, '時系列データ取得に失敗しました')

    @app.route('/api/monitoring/visualize/dashboard')
    def get_dashboard_visualization():
        """ダッシュボード可視化データAPI"""
        try:
            hours = request.args.get('hours', 24, type=int)
            data = metrics_visualizer.get_dashboard_data(hours)
            return jsonify(data)
        except Exception as e:
            app.logger.error(f"Dashboard visualization API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'ダッシュボードデータ取得に失敗しました')

    @app.route('/api/monitoring/visualize/histogram')
    def get_metric_histogram():
        """メトリクスヒストグラムAPI"""
        try:
            metric_name = request.args.get('metric')
            hours = request.args.get('hours', 24, type=int)
            bins = request.args.get('bins', 20, type=int)
            
            if not metric_name:
                return security_manager.create_error_response(400, 'メトリクス名が必要です')
            
            data = metrics_visualizer.get_metric_histogram(metric_name, hours, bins)
            return jsonify(data)
            
        except Exception as e:
            app.logger.error(f"Histogram API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'ヒストグラム取得に失敗しました')

    @app.route('/api/monitoring/visualize/correlation')
    def get_correlation_matrix():
        """相関行列API"""
        try:
            metric_names = request.args.getlist('metrics')
            hours = request.args.get('hours', 24, type=int)
            
            if len(metric_names) < 2:
                return security_manager.create_error_response(400, '最低2つのメトリクス名が必要です')
            
            data = metrics_visualizer.get_correlation_matrix(metric_names, hours)
            return jsonify(data)
            
        except Exception as e:
            app.logger.error(f"Correlation API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, '相関行列取得に失敗しました')

    @app.route('/api/monitoring/visualize/anomalies')
    def get_anomaly_detection():
        """異常検知API"""
        try:
            metric_name = request.args.get('metric')
            hours = request.args.get('hours', 24, type=int)
            sensitivity = request.args.get('sensitivity', 2.0, type=float)
            
            if not metric_name:
                return security_manager.create_error_response(400, 'メトリクス名が必要です')
            
            data = metrics_visualizer.get_anomaly_detection(metric_name, hours, sensitivity)
            return jsonify(data)
            
        except Exception as e:
            app.logger.error(f"Anomaly detection API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, '異常検知に失敗しました')

    @app.route('/api/monitoring/export')
    def export_metrics():
        """メトリクスエクスポートAPI"""
        try:
            metric_names = request.args.getlist('metrics')
            hours = request.args.get('hours', 24, type=int)
            format_type = request.args.get('format', 'json')
            
            if not metric_names:
                return security_manager.create_error_response(400, 'メトリクス名が必要です')
            
            data = metrics_visualizer.export_metrics_data(metric_names, hours, format_type)
            
            if format_type.lower() == 'csv':
                response = app.response_class(
                    data,
                    mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=metrics.csv'}
                )
                return response
            else:
                return jsonify({'data': data})
                
        except Exception as e:
            app.logger.error(f"Export API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'エクスポートに失敗しました')

    # キャッシュ管理API
    @app.route('/api/cache/stats')
    def get_cache_stats():
        """キャッシュ統計API"""
        try:
            overview = cache_strategies.get_cache_overview()
            return jsonify(overview)
        except Exception as e:
            app.logger.error(f"Cache stats API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'キャッシュ統計取得に失敗しました')

    @app.route('/api/cache/health')
    def get_cache_health():
        """キャッシュヘルスチェックAPI"""
        try:
            health = cache_manager.health_check()
            status_code = 200 if health['status'] == 'healthy' else 503
            return jsonify(health), status_code
        except Exception as e:
            app.logger.error(f"Cache health API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'キャッシュヘルスチェックに失敗しました')

    @app.route('/api/cache/invalidate/user/<int:user_id>', methods=['POST'])
    def invalidate_user_cache(user_id):
        """ユーザーキャッシュ無効化API"""
        try:
            results = cache_strategies.invalidate_all_user_cache(user_id)
            total_deleted = sum(results.values())
            
            return jsonify({
                'success': True,
                'user_id': user_id,
                'deleted_entries': results,
                'total_deleted': total_deleted,
                'message': f'{total_deleted} cache entries invalidated'
            })
        except Exception as e:
            app.logger.error(f"Cache invalidation API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'キャッシュ無効化に失敗しました')

    @app.route('/api/cache/warmup', methods=['POST'])
    def warmup_cache():
        """キャッシュウォームアップAPI"""
        try:
            warmed_keys = cache_strategies.warm_up_common_data()
            
            return jsonify({
                'success': True,
                'warmed_keys': warmed_keys,
                'message': f'{warmed_keys} cache entries warmed up'
            })
        except Exception as e:
            app.logger.error(f"Cache warmup API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'キャッシュウォームアップに失敗しました')

    @app.route('/api/cache/cleanup', methods=['POST'])
    def cleanup_cache():
        """キャッシュクリーンアップAPI"""
        try:
            results = cache_strategies.cleanup_expired_cache()
            
            return jsonify({
                'success': True,
                'cleanup_results': results,
                'message': 'Cache cleanup completed'
            })
        except Exception as e:
            app.logger.error(f"Cache cleanup API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'キャッシュクリーンアップに失敗しました')

    # 静的ファイル最適化API
    @app.route('/api/optimization/stats')
    def get_optimization_stats():
        """最適化統計API"""
        try:
            stats = static_optimizer.get_optimization_stats()
            return jsonify(stats)
        except Exception as e:
            app.logger.error(f"Optimization stats API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, '最適化統計取得に失敗しました')

    @app.route('/api/optimization/optimize', methods=['POST'])
    def optimize_files():
        """ファイル最適化API"""
        try:
            data = request.get_json() or {}
            
            if 'file_path' in data:
                # 単一ファイルの最適化
                result = static_optimizer.optimize_file(data['file_path'])
            elif 'directory' in data:
                # ディレクトリの最適化
                file_patterns = data.get('patterns', ['*.css', '*.js', '*.jpg', '*.jpeg', '*.png'])
                result = static_optimizer.optimize_directory(data['directory'], file_patterns)
            else:
                return security_manager.create_error_response(400, 'file_path または directory が必要です')
            
            return jsonify(result)
            
        except Exception as e:
            app.logger.error(f"File optimization API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'ファイル最適化に失敗しました')

    @app.route('/api/optimization/manifest', methods=['POST'])
    def create_asset_manifest():
        """アセットマニフェスト作成API"""
        try:
            data = request.get_json() or {}
            assets_dir = data.get('assets_dir', 'static')
            
            result = static_optimizer.create_asset_manifest(assets_dir)
            return jsonify(result)
            
        except Exception as e:
            app.logger.error(f"Asset manifest API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'アセットマニフェスト作成に失敗しました')

    @app.route('/api/optimization/cdn-url')
    def get_cdn_url():
        """CDN URL取得API"""
        try:
            asset_path = request.args.get('path')
            asset_type = request.args.get('type')
            
            if not asset_path:
                return security_manager.create_error_response(400, 'path パラメータが必要です')
            
            cdn_url = static_optimizer.cdn_manager.get_cdn_url(asset_path, asset_type)
            cache_headers = static_optimizer.cdn_manager.get_cache_headers(
                asset_type or static_optimizer.cdn_manager._detect_asset_type(asset_path)
            )
            
            return jsonify({
                'original_path': asset_path,
                'cdn_url': cdn_url,
                'cache_headers': cache_headers,
                'asset_type': asset_type or static_optimizer.cdn_manager._detect_asset_type(asset_path)
            })
            
        except Exception as e:
            app.logger.error(f"CDN URL API error: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'CDN URL取得に失敗しました')

    @app.route('/analyze', methods=['POST'])
    def analyze_account():
        """Xアカウント分析API（キャッシュ統合版）"""
        # テスト環境ではリクエスト検証をスキップ
        if not app.config.get('TESTING', False):
            if not security_manager.validate_request(request):
                return security_manager.create_error_response(400, "Invalid request")
        
        data = request.get_json()
        username = data.get('username', '').replace('@', '')
        
        if not username:
            return security_manager.create_error_response(400, 'ユーザー名が必要です')
        
        # キャッシュから分析結果を確認
        cached_result = cache_strategies.analysis_results.get_twitter_analysis(username)
        if cached_result:
            app.logger.info(f"Analysis cache hit for user: {username}")
            monitoring_manager.record_counter("analysis.cache.hits", 1)
            return jsonify(cached_result)
        
        # 分析開始メトリクス
        monitoring_manager.record_counter("analysis.requests.total", 1, {'username': username})
        monitoring_manager.record_counter("analysis.cache.misses", 1)
        analysis_start_time = time.time()
        
        try:
            # Twitter分析を実行
            result = analyze_twitter_account(username, security_manager)
            
            if result.get('status') == 'success':
                # データベースに保存
                save_analysis_to_database(result, user_repo, analysis_repo, interests_skills_repo)
                
                # マッチング候補を追加
                user = user_repo.get_user_by_username(username)
                if user:
                    # マッチング結果もキャッシュから確認
                    cached_matches = cache_strategies.matching_results.get_user_matches(user['id'], 3)
                    if cached_matches:
                        result['matches'] = cached_matches['matches']
                        monitoring_manager.record_counter("matching.cache.hits", 1)
                    else:
                        matches = matching_engine.find_potential_matches(user['id'], limit=3)
                        result['matches'] = matches
                        # マッチング結果をキャッシュ
                        cache_strategies.matching_results.set_user_matches(user['id'], matches, 3)
                        monitoring_manager.record_counter("matching.cache.misses", 1)
                
                # 分析結果をキャッシュ
                cache_strategies.analysis_results.set_twitter_analysis(username, result)
                
                # 成功メトリクス
                analysis_duration = (time.time() - analysis_start_time) * 1000
                monitoring_manager.record_timer("analysis.duration", analysis_duration, {'status': 'success'})
                monitoring_manager.record_counter("analysis.success.total", 1)
            else:
                # エラーメトリクス
                monitoring_manager.record_counter("analysis.errors.total", 1, {'error_type': 'analysis_failed'})
            
            return jsonify(result)
        except Exception as e:
            # エラーメトリクス
            analysis_duration = (time.time() - analysis_start_time) * 1000
            monitoring_manager.record_timer("analysis.duration", analysis_duration, {'status': 'error'})
            monitoring_manager.record_counter("analysis.errors.total", 1, {'error_type': type(e).__name__})
            
            app.logger.error(f"Analysis error for user {username}: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'サーバーエラーが発生しました')

    @app.route('/matches/<username>')
    def get_matches(username):
        """学友マッチング結果API（キャッシュ統合版）"""
        try:
            username = username.replace('@', '')
            user = user_repo.get_user_by_username(username)
            
            if not user:
                return security_manager.create_error_response(404, 'ユーザーが見つかりません')
            
            # キャッシュからマッチング結果を確認
            cached_matches = cache_strategies.matching_results.get_user_matches(user['id'], 5)
            if cached_matches:
                app.logger.info(f"Matching cache hit for user: {username}")
                monitoring_manager.record_counter("matching.cache.hits", 1)
                return jsonify({
                    'username': username,
                    'matches': cached_matches['matches'],
                    'total_matches': len(cached_matches['matches']),
                    'cached': True,
                    'generated_at': cached_matches['generated_at']
                })
            
            # マッチング候補を取得
            monitoring_manager.record_counter("matching.cache.misses", 1)
            matches = matching_engine.find_potential_matches(user['id'], limit=5)
            
            # 結果をキャッシュ
            cache_strategies.matching_results.set_user_matches(user['id'], matches, 5)
            
            return jsonify({
                'username': username,
                'matches': matches,
                'total_matches': len(matches),
                'cached': False
            })
        except Exception as e:
            app.logger.error(f"Matches error for user {username}: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'サーバーエラーが発生しました')

def register_error_handlers(app, security_manager):
    """エラーハンドラーの登録"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 error: {request.url}")
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 error: {error}", exc_info=True)
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(429)
    def rate_limit_error(error):
        app.logger.warning(f"Rate limit exceeded: {request.remote_addr}")
        return security_manager.create_error_response(
            429, 
            'レート制限に達しました。しばらく待ってから再試行してください。',
            {'retry_after': getattr(error, 'retry_after', 60)}
        )
    
    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f"403 error: {request.url}")
        return security_manager.create_error_response(403, 'アクセスが拒否されました')

def save_analysis_to_database(analysis_result, user_repo, analysis_repo, interests_skills_repo):
    """分析結果をデータベースに保存"""
    try:
        username = analysis_result['username']
        account_data = analysis_result['account_data']
        
        # ユーザーを作成または更新
        user_id = user_repo.create_or_update_user(account_data)
        
        # 分析結果を保存
        analysis_repo.save_analysis(user_id, analysis_result)
        
        # 興味・スキルを抽出・保存
        interests_skills_repo.extract_and_save_interests_skills(user_id, analysis_result)
        
        logging.info(f"✅ データベース保存完了: @{username} (ID: {user_id})")
        
    except Exception as e:
        logging.error(f"❌ データベース保存エラー: {e}", exc_info=True)
        raise

def analyze_twitter_account(username, security_manager):
    """Twitter アカウント分析（実際のAPI使用）"""
    from twitter_api import get_twitter_client
    
    # Twitter API クライアントを取得（セキュアなAPIキー取得）
    twitter_token = security_manager.get_api_key('twitter')
    if not twitter_token:
        return {
            "username": username,
            "error": "Twitter APIキーが設定されていません",
            "status": "error"
        }
    
    twitter_client = get_twitter_client()
    
    # 実際のアカウントデータを取得
    twitter_data = twitter_client.get_full_user_data(username)
    
    if not twitter_data:
        return {
            "username": username,
            "error": "アカウントが見つからないか、取得に失敗しました",
            "status": "error"
        }
    
    user_info = twitter_data['user_info']
    tweets_text = twitter_data['tweet_text_combined']
    
    # 実際のデータを使用
    account_data = {
        "name": user_info['name'],
        "username": user_info['username'],
        "bio": user_info['description'],
        "followers": user_info['followers_count'],
        "following": user_info['following_count'],
        "location": user_info.get('location', ''),
        "tweet_count": user_info['tweet_count'],
        "verified": user_info.get('verified', False),
        "recent_tweets": tweets_text[:500] + "..." if len(tweets_text) > 500 else tweets_text
    }
    
    # Gemini API で分析（より詳細なプロンプト）
    prompt = f"""
    以下の実際のXアカウント情報を分析して、東京通信大学の学生マッチングに必要な情報を抽出してください：

    【プロフィール情報】
    名前: {account_data['name']}
    ユーザー名: @{account_data['username']}
    自己紹介: {account_data['bio']}
    所在地: {account_data['location']}
    フォロワー数: {account_data['followers']}
    フォロー数: {account_data['following']}
    ツイート数: {account_data['tweet_count']}
    認証済み: {account_data['verified']}
    
    【最近の投稿内容（抜粋）】
    {account_data['recent_tweets']}
    
    以下の項目について分析し、JSON形式で回答してください：
    {{
        "university_relation": "高/中/低/不明",
        "university_relation_reason": "判定理由",
        "relation_type": "学生/教員/職員/卒業生/関係者/その他",
        "interests": ["興味分野1", "興味分野2", "興味分野3"],
        "major_field": "情報学/経営学/人文学/その他/不明",
        "personality_traits": ["性格特徴1", "性格特徴2"],
        "learning_style": "学習スタイルの説明",
        "activity_pattern": "活動パターンの説明",
        "tech_skills": ["技術スキル1", "技術スキル2"],
        "collaboration_potential": "協働可能性の評価"
    }}
    
    注意：
    - 東京通信大学への言及、学習関連の投稿、技術的な内容を重視してください
    - プライバシーに配慮し、推測に基づく分析であることを明記してください
    - 不明な項目は「不明」または「推測困難」と記載してください
    """
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        return {
            "username": username,
            "account_data": account_data,
            "raw_twitter_data": twitter_data,  # デバッグ用
            "analysis": response.text,
            "status": "success"
        }
        
    except Exception as e:
        return {
            "username": username,
            "account_data": account_data,
            "error": f"AI分析エラー: {str(e)}",
            "status": "error"
        }

# アプリケーションインスタンスの作成
app = create_app()

if __name__ == '__main__':
    environment = os.getenv('ENVIRONMENT', 'development')
    
    if environment == 'development':
        app.run(debug=True, port=5002)
    else:
        # 本番環境ではGunicornを使用
        print("本番環境ではGunicornを使用してください:")
        print("gunicorn -w 4 -b 0.0.0.0:5000 app:app")