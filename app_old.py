import os
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

# セキュリティ・設定関連のインポート
from security.security_manager import init_security
from config.production_config import get_config

# データベース関連のインポート
from database.database_manager import DatabaseManager
from repositories.user_repository import UserRepository
from repositories.analysis_repository import AnalysisRepository
from repositories.interests_skills_repository import InterestsSkillsRepository
from matching.matching_engine import MatchingEngine
from learning_resources.resource_recommender import LearningResourceRecommender

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
    
    # Gemini API設定
    api_key = security_manager.get_api_key('gemini')
    if not api_key:
        raise ValueError("GEMINI_API_KEY が設定されていません")
    
    genai.configure(api_key=api_key)
    
    # データベース初期化
    db_url = app.config.get('DATABASE_URL', 'sqlite:///tou_connect.db')
    if db_url.startswith('sqlite'):
        db_path = db_url.replace('sqlite:///', '')
        db = DatabaseManager(db_path)
    else:
        # PostgreSQL等の場合は接続文字列をそのまま使用
        db = DatabaseManager(db_url)
    
    # リポジトリの初期化
    user_repo = UserRepository(db)
    analysis_repo = AnalysisRepository(db)
    interests_skills_repo = InterestsSkillsRepository(db)
    matching_engine = MatchingEngine(db)
    resource_recommender = LearningResourceRecommender(db)
    
    # ルートの登録
    register_routes(app, security_manager, user_repo, analysis_repo, 
                   interests_skills_repo, matching_engine, resource_recommender)
    
    # エラーハンドラーの登録
    register_error_handlers(app, security_manager)
    
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
                   interests_skills_repo, matching_engine, resource_recommender):
    """ルートの登録"""

# Gemini API設定
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY が設定されていません")

genai.configure(api_key=api_key)

# データベース初期化
db = DatabaseManager("tou_connect.db")
user_repo = UserRepository(db)
analysis_repo = AnalysisRepository(db)
interests_skills_repo = InterestsSkillsRepository(db)
matching_engine = MatchingEngine(db)
resource_recommender = LearningResourceRecommender(db)

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

    @app.route('/health')
    def health_check():
        """ヘルスチェックエンドポイント"""
        try:
            # データベース接続チェック
            db_status = "ok"
            try:
                # 簡単なクエリでDB接続を確認
                user_repo.get_user_by_username("health_check_dummy")
                db_status = "ok"
            except Exception:
                db_status = "error"
            
            # 外部API接続チェック
            api_status = "ok"
            gemini_key = security_manager.get_api_key('gemini')
            twitter_key = security_manager.get_api_key('twitter')
            
            if not gemini_key or not twitter_key:
                api_status = "warning"
            
            health_data = {
                "status": "healthy" if db_status == "ok" and api_status == "ok" else "degraded",
                "timestamp": "2024-01-01T00:00:00Z",  # 実際の実装では現在時刻
                "services": {
                    "database": db_status,
                    "external_apis": api_status
                }
            }
            
            status_code = 200 if health_data["status"] == "healthy" else 503
            return jsonify(health_data), status_code
            
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "error": str(e)
            }), 503

    @app.route('/analyze', methods=['POST'])
    @security_manager.rate_limit_decorator("10 per minute")
    def analyze_account():
        """Xアカウント分析API（データベース統合版）"""
        # リクエスト検証
        if not security_manager.validate_request(request):
            return security_manager.create_error_response(400, "Invalid request")
        
        data = request.get_json()
        username = data.get('username', '').replace('@', '')
        
        if not username:
            return security_manager.create_error_response(400, 'ユーザー名が必要です')
        
        try:
            # Twitter分析を実行
            result = analyze_twitter_account(username, security_manager)
            
            if result.get('status') == 'success':
                # データベースに保存
                save_analysis_to_database(result, user_repo, analysis_repo, interests_skills_repo)
                
                # マッチング候補を追加
                user = user_repo.get_user_by_username(username)
                if user:
                    matches = matching_engine.find_potential_matches(user['id'], limit=3)
                    result['matches'] = matches
            
            return jsonify(result)
        except Exception as e:
            app.logger.error(f"Analysis error for user {username}: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'サーバーエラーが発生しました')

    @app.route('/matches/<username>')
    @security_manager.rate_limit_decorator("20 per minute")
    def get_matches(username):
        """学友マッチング結果API"""
        try:
            username = username.replace('@', '')
            user = user_repo.get_user_by_username(username)
            
            if not user:
                return security_manager.create_error_response(404, 'ユーザーが見つかりません')
            
            # マッチング候補を取得
            matches = matching_engine.find_potential_matches(user['id'], limit=5)
            
            return jsonify({
                'username': username,
                'matches': matches,
                'total_matches': len(matches)
            })
        except Exception as e:
            app.logger.error(f"Matches error for user {username}: {e}", exc_info=True)
            return security_manager.create_error_response(500, 'サーバーエラーが発生しました')

@app.route('/profile/<username>')
def get_profile(username):
    """完全プロフィール取得API"""
    try:
        username = username.replace('@', '')
        user = user_repo.get_user_by_username(username)
        
        if not user:
            return jsonify({'error': 'ユーザーが見つかりません'}), 404
        
        # 分析結果を取得
        analysis = analysis_repo.get_latest_analysis(user['id'])
        interests = interests_skills_repo.get_user_interests(user['id'])
        skills = interests_skills_repo.get_user_skills(user['id'])
        
        # 学習リソース推薦を追加
        recommendations = resource_recommender.get_recommendations(user['id'], limit=3)
        
        return jsonify({
            'user': user,
            'analysis': analysis,
            'interests': interests,
            'skills': skills,
            'recommended_resources': recommendations
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/resources/<username>')
def get_learning_resources(username):
    """学習リソース推薦API"""
    try:
        username = username.replace('@', '')
        user = user_repo.get_user_by_username(username)
        
        if not user:
            return jsonify({'error': 'ユーザーが見つかりません'}), 404
        
        # 個別推薦
        recommendations = resource_recommender.get_recommendations(user['id'], limit=5)
        
        # 人気リソース
        popular_resources = resource_recommender.get_popular_resources(limit=5)
        
        return jsonify({
            'username': username,
            'recommendations': recommendations,
            'popular_resources': popular_resources
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/resources/click', methods=['POST'])
def track_resource_click():
    """アフィリエイトクリック追跡API"""
    try:
        data = request.get_json()
        username = data.get('username', '').replace('@', '')
        resource_title = data.get('resource_title', '')
        affiliate_url = data.get('affiliate_url', '')
        
        user = user_repo.get_user_by_username(username)
        if user:
            resource_recommender.track_click(user['id'], resource_title, affiliate_url)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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