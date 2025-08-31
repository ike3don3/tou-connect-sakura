"""
キャッシュ管理エンドポイント
管理者向けキャッシュシステムの監視・管理機能
"""

from flask import Blueprint, jsonify, request
from functools import wraps
import logging

from cache.cache_factory import get_cache_factory, get_cache_stats, is_cache_available

cache_admin_bp = Blueprint('cache_admin', __name__, url_prefix='/admin/cache')
logger = logging.getLogger(__name__)


def admin_required(f):
    """管理者権限確認デコレータ（簡易版）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 実際のプロジェクトでは適切な権限確認を実装
        api_key = request.headers.get('X-Admin-API-Key')
        if not api_key or api_key != "admin_secret_key":  # 本番では環境変数から取得
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function


@cache_admin_bp.route('/status', methods=['GET'])
@admin_required
def cache_status():
    """キャッシュシステムの状態確認"""
    try:
        stats = get_cache_stats()
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        logger.error(f"Cache status error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@cache_admin_bp.route('/health', methods=['GET'])
def cache_health():
    """キャッシュシステムのヘルスチェック（認証不要）"""
    try:
        factory = get_cache_factory()
        cache_manager = factory.cache_manager
        
        if cache_manager:
            health = cache_manager.health_check()
        else:
            health = {"status": "unavailable", "message": "Cache manager not initialized"}
        
        return jsonify({
            "success": True,
            "data": health
        })
    except Exception as e:
        logger.error(f"Cache health check error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@cache_admin_bp.route('/clear', methods=['POST'])
@admin_required
def clear_cache():
    """キャッシュのクリア"""
    try:
        cache_type = request.json.get('cache_type') if request.json else None
        factory = get_cache_factory()
        
        if cache_type:
            success = factory.clear_cache_by_type(cache_type)
            message = f"Cache type '{cache_type}' cleared" if success else "Failed to clear cache"
        else:
            success = factory.clear_all_cache()
            message = "All cache cleared" if success else "Failed to clear cache"
        
        return jsonify({
            "success": success,
            "message": message
        })
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@cache_admin_bp.route('/stats', methods=['GET'])
@admin_required
def cache_stats():
    """詳細なキャッシュ統計情報"""
    try:
        factory = get_cache_factory()
        cache_manager = factory.cache_manager
        
        if not cache_manager:
            return jsonify({
                "success": False,
                "error": "Cache manager not available"
            }), 503
        
        stats = cache_manager.get_stats()
        
        # 追加の統計情報
        extended_stats = {
            **stats,
            "cache_available": is_cache_available(),
            "strategies": {
                "user_data": factory.user_data_cache is not None,
                "analysis_cache": factory.analysis_cache is not None,
            }
        }
        
        return jsonify({
            "success": True,
            "data": extended_stats
        })
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@cache_admin_bp.route('/metrics', methods=['GET'])
@admin_required
def cache_metrics():
    """キャッシュメトリクス（Prometheus形式）"""
    try:
        factory = get_cache_factory()
        cache_manager = factory.cache_manager
        
        if not cache_manager:
            return "# Cache manager not available\n", 503, {'Content-Type': 'text/plain'}
        
        stats = cache_manager.get_stats()
        
        # Prometheus形式のメトリクス
        metrics = []
        metrics.append(f"# HELP cache_hits_total Total number of cache hits")
        metrics.append(f"# TYPE cache_hits_total counter")
        metrics.append(f"cache_hits_total {stats.get('hits', 0)}")
        
        metrics.append(f"# HELP cache_misses_total Total number of cache misses")
        metrics.append(f"# TYPE cache_misses_total counter") 
        metrics.append(f"cache_misses_total {stats.get('misses', 0)}")
        
        metrics.append(f"# HELP cache_hit_rate Cache hit rate percentage")
        metrics.append(f"# TYPE cache_hit_rate gauge")
        metrics.append(f"cache_hit_rate {stats.get('hit_rate', 0)}")
        
        metrics.append(f"# HELP cache_errors_total Total number of cache errors")
        metrics.append(f"# TYPE cache_errors_total counter")
        metrics.append(f"cache_errors_total {stats.get('errors', 0)}")
        
        metrics.append(f"# HELP cache_connected Cache connection status")
        metrics.append(f"# TYPE cache_connected gauge")
        metrics.append(f"cache_connected {1 if stats.get('connected', False) else 0}")
        
        return "\n".join(metrics) + "\n", 200, {'Content-Type': 'text/plain'}
        
    except Exception as e:
        logger.error(f"Cache metrics error: {e}")
        return f"# Error: {str(e)}\n", 500, {'Content-Type': 'text/plain'}


@cache_admin_bp.route('/config', methods=['GET'])
@admin_required
def cache_config():
    """キャッシュ設定情報"""
    try:
        factory = get_cache_factory()
        
        config_info = {
            "environment": factory.environment,
            "strategies": factory.config.get("strategies", {}),
            "redis_config": {
                "url": factory.config["redis"]["url"].replace(
                    factory.config["redis"]["url"].split('@')[-1] if '@' in factory.config["redis"]["url"] else '',
                    '***masked***'
                ),  # パスワードをマスク
                "max_connections": factory.config["redis"].get("max_connections"),
            },
            "monitoring": factory.config.get("monitoring", {})
        }
        
        return jsonify({
            "success": True,
            "data": config_info
        })
    except Exception as e:
        logger.error(f"Cache config error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def register_cache_admin_routes(app):
    """キャッシュ管理ルートの登録"""
    app.register_blueprint(cache_admin_bp)
    logger.info("Cache admin routes registered")
