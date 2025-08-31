#!/usr/bin/env python3
"""
TOU Connect - 緊急デプロイ用シンプル版
基本機能のみでデプロイ可能なバージョン
"""

import os
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from twitter_api import TwitterAPI
from real_account_database import get_matching_accounts, REAL_EDUCATION_ACCOUNTS

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数読み込み
if os.getenv('ENVIRONMENT', 'development') == 'development':
    load_dotenv()

def analyze_interests_from_description(description):
    """プロフィール説明文から興味・関心を推定"""
    interests = []
    
    # キーワードベースの簡易分析
    keywords_map = {
        "プログラミング": ["プログラミング", "コーディング", "開発", "エンジニア", "coding", "programming", "developer"],
        "教育": ["教育", "学習", "教師", "先生", "学校", "大学", "education", "learning", "teacher"],
        "テクノロジー": ["技術", "テクノロジー", "AI", "機械学習", "tech", "technology", "IT"],
        "ビジネス": ["ビジネス", "経営", "マーケティング", "business", "marketing", "起業"],
        "デザイン": ["デザイン", "UI", "UX", "グラフィック", "design", "creative"],
        "研究": ["研究", "論文", "学術", "research", "academic", "科学"],
        "読書": ["読書", "本", "書籍", "reading", "book"],
        "音楽": ["音楽", "音響", "music", "sound"],
        "スポーツ": ["スポーツ", "運動", "fitness", "health"],
        "言語": ["言語", "英語", "日本語", "language", "english"]
    }
    
    description_lower = description.lower()
    
    for interest, keywords in keywords_map.items():
        if any(keyword.lower() in description_lower for keyword in keywords):
            interests.append(interest)
    
    # デフォルトの興味を追加（空の場合）
    if not interests:
        interests = ["学習", "自己成長", "情報収集"]
    
    return interests[:5]  # 最大5個まで

def estimate_learning_style(user_info):
    """ユーザー情報から学習スタイルを推定"""
    description = user_info.get('description', '').lower()
    followers_count = user_info.get('followers_count', 0)
    
    # フォロワー数による傾向分析
    if followers_count > 10000:
        return "情報発信型学習者"
    elif followers_count > 1000:
        return "コミュニティ型学習者"
    
    # プロフィール内容による分析
    if any(word in description for word in ["研究", "academic", "論文", "university"]):
        return "学術的学習者"
    elif any(word in description for word in ["実践", "hands-on", "project", "開発"]):
        return "実践的学習者"
    elif any(word in description for word in ["視覚", "図解", "visual", "グラフィック"]):
        return "視覚的学習者"
    else:
        return "バランス型学習者"

def estimate_personality_traits(user_info):
    """性格特性を推定"""
    description = user_info.get('description', '').lower()
    traits = []
    
    # キーワードによる性格推定
    if any(word in description for word in ["好奇心", "curious", "探究", "学習"]):
        traits.append("好奇心旺盛")
    if any(word in description for word in ["チーム", "協力", "collaboration", "community"]):
        traits.append("協調性")
    if any(word in description for word in ["計画", "目標", "systematic", "organized"]):
        traits.append("計画性")
    if any(word in description for word in ["創造", "creative", "innovative", "アイデア"]):
        traits.append("創造性")
    if any(word in description for word in ["継続", "persistent", "継続的", "習慣"]):
        traits.append("継続性")
    
    # デフォルト特性
    if not traits:
        traits = ["学習意欲", "向上心"]
    
    return traits[:3]  # 最大3個まで

def estimate_study_preferences(interests):
    """興味から学習の好みを推定"""
    preferences = []
    
    if "プログラミング" in interests or "テクノロジー" in interests:
        preferences.extend(["実践的学習", "プロジェクト学習"])
    if "教育" in interests or "研究" in interests:
        preferences.extend(["体系的学習", "深い理解"])
    if "デザイン" in interests:
        preferences.extend(["視覚的学習", "創造的学習"])
    if "ビジネス" in interests:
        preferences.extend(["実用的学習", "ケーススタディ"])
    
    # 基本的な学習形態を追加
    preferences.extend(["オンライン学習", "自主学習"])
    
    return list(set(preferences))[:4]  # 重複除去、最大4個

def estimate_activity_level(user_info):
    """活動レベルを推定"""
    tweets_count = user_info.get('tweet_count', 0)
    followers_count = user_info.get('followers_count', 0)
    
    if tweets_count > 10000 or followers_count > 5000:
        return "高活動"
    elif tweets_count > 1000 or followers_count > 500:
        return "中程度"
    else:
        return "低〜中程度"

def estimate_engagement_pattern(user_info):
    """エンゲージメントパターンを推定"""
    # 簡易版：アカウント作成時期やプロフィールから推定
    description = user_info.get('description', '').lower()
    
    if any(word in description for word in ["夜", "night", "evening"]):
        return "夜間活動型"
    elif any(word in description for word in ["朝", "morning", "早起き"]):
        return "朝型活動"
    else:
        return "日中活動型"

def estimate_interests_from_username(username):
    """ユーザー名から興味・関心を推定"""
    interests = []
    username_lower = username.lower()
    
    # ユーザー名の特徴から興味を推定
    keywords_map = {
        "プログラミング": ["code", "dev", "program", "tech", "coding", "developer", "engineer", "python", "java", "js"],
        "教育": ["edu", "learn", "study", "teacher", "student", "academic", "school", "univ"],
        "テクノロジー": ["tech", "digital", "ai", "ml", "data", "web", "mobile", "it", "computer"],
        "ビジネス": ["business", "marketing", "sales", "startup", "entrepreneur", "manager"],
        "デザイン": ["design", "ui", "ux", "creative", "art", "visual", "graphic"],
        "研究": ["research", "science", "lab", "phd", "academic", "scholar"],
        "ゲーム": ["game", "gaming", "player", "gamer", "play"],
        "音楽": ["music", "sound", "audio", "musician", "song", "beat"],
        "スポーツ": ["sport", "fitness", "health", "athlete", "gym", "run"],
        "言語": ["lang", "japanese", "english", "translation", "linguist"]
    }
    
    for interest, keywords in keywords_map.items():
        if any(keyword in username_lower for keyword in keywords):
            interests.append(interest)
    
    # 特定パターンの追加分析
    if "3" in username or "don" in username_lower:
        # 創造性や個性を示すパターン
        if "テクノロジー" not in interests:
            interests.append("テクノロジー")
        if "教育" not in interests:
            interests.append("教育")
    
    # 数字パターンの分析
    if any(char.isdigit() for char in username):
        if not interests:  # 他に興味が見つからない場合
            interests.append("テクノロジー")
    
    # デフォルトの興味を追加（空の場合）
    if not interests:
        interests = ["学習", "自己成長", "コミュニティ"]
    
    return interests[:4]  # 最大4個まで

def create_simple_app():
    """シンプルなFlaskアプリケーションの作成"""
    app = Flask(__name__)
    
    # Twitter API初期化
    twitter_api = TwitterAPI()
    
    # 基本設定
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-this')
    app.config['DEBUG'] = os.getenv('ENVIRONMENT', 'development') == 'development'
    
    @app.route('/')
    def home():
        """ホームページ"""
        return render_template('index.html', title='TOU Connect')
    
    @app.route('/health')
    def health_check():
        """ヘルスチェックエンドポイント"""
        return jsonify({
            "status": "healthy",
            "message": "TOU Connect is running",
            "version": "1.0.0-simple"
        })
    
    @app.route('/api/status')
    def api_status():
        """API状態確認"""
        return jsonify({
            "api_status": "operational",
            "features": {
                "basic_routes": True,
                "health_check": True,
                "static_files": True
            },
            "environment": os.getenv('ENVIRONMENT', 'development')
        })
    
    @app.route('/api/consent', methods=['POST'])
    def consent():
        """同意情報の記録"""
        try:
            consent_data = request.get_json()
            
            # 同意データの検証
            required_fields = ['privacy_policy', 'terms_of_service', 'ai_analysis']
            if not all(consent_data.get(field) for field in required_fields):
                return jsonify({"success": False, "error": "すべての項目への同意が必要です"}), 400
            
            # 実際の実装では、ここでデータベースに保存
            logger.info(f"Consent recorded: {consent_data}")
            
            return jsonify({
                "success": True,
                "message": "同意が記録されました",
                "timestamp": consent_data.get('timestamp')
            })
            
        except Exception as e:
            logger.error(f"Consent recording error: {e}")
            return jsonify({"success": False, "error": "内部エラーが発生しました"}), 500
    
    @app.route('/api/consent/status')
    def consent_status():
        """同意状況の確認"""
        # 実際の実装では、ユーザーの同意状況をデータベースから確認
        # 簡易版では常に同意が必要として返す
        return jsonify({
            "consent_required": True,
            "privacy_policy": False,
            "terms_of_service": False,
            "ai_analysis": False
        })
    
    @app.route('/api/analyze', methods=['POST'])
    def analyze_account():
        """アカウント分析エンドポイント"""
        try:
            data = request.get_json()
            logger.info(f"Received analysis request: {data}")
            
            if not data:
                logger.error("No JSON data received")
                return jsonify({"success": False, "error": "データが送信されていません"}), 400
            
            username = data.get('username', '').strip()
            logger.info(f"Processing username: '{username}'")
            
            if not username:
                logger.error("Username is empty")
                return jsonify({"success": False, "error": "ユーザー名が指定されていません"}), 400
            
            # ユーザー名の検証
            import re
            username_pattern = r'^[a-zA-Z0-9_]{1,15}$'
            if not re.match(username_pattern, username):
                logger.error(f"Invalid username pattern: '{username}' does not match {username_pattern}")
                return jsonify({"success": False, "error": f"無効なユーザー名です: '{username}'"}), 400
            
            # 実際のTwitterアカウント情報を取得
            user_info = None
            if twitter_api.client:
                logger.info(f"Fetching real Twitter data for: {username}")
                user_info = twitter_api.get_user_by_username(username)
            
            if user_info:
                # 実際のアカウント情報を使用
                logger.info(f"Real account found: @{user_info['username']}")
                
                # プロフィールから興味・関心を推定（簡易版）
                interests = analyze_interests_from_description(user_info.get('description', ''))
                learning_style = estimate_learning_style(user_info)
                
                logger.info(f"Detected interests for {username}: {interests}")
                logger.info(f"Detected learning style for {username}: {learning_style}")
                
                # 実在するアカウントとマッチング
                matches = get_matching_accounts(interests, learning_style, max_matches=5)
                logger.info(f"Matching results for {username}: {len(matches)} matches found")
                for match in matches:
                    logger.info(f"  - @{match['username']}: {match['compatibility_score']}%")
                
                analysis_result = {
                    "username": user_info['username'],
                    "display_name": user_info['name'],
                    "followers_count": user_info['followers_count'],
                    "following_count": user_info['following_count'],
                    "tweets_count": user_info['tweet_count'],
                    "account_created": user_info['created_at'][:10] if user_info['created_at'] else "不明",
                    "verified": user_info['verified'],
                    "profile_image_url": user_info.get('profile_image_url', ''),
                    "description": user_info.get('description', ''),
                    "location": user_info.get('location', ''),
                    "analysis": {
                        "interests": interests,
                        "learning_style": learning_style,
                        "personality_traits": estimate_personality_traits(user_info),
                        "study_preferences": estimate_study_preferences(interests),
                        "activity_level": estimate_activity_level(user_info),
                        "engagement_pattern": estimate_engagement_pattern(user_info)
                    },
                    "matches": matches
                }
                
            else:
                # TwitterAPIが利用できない場合、またはアカウントが見つからない場合
                logger.warning(f"Twitter API unavailable or account not found: {username}")
                
                # ユーザー名から推定される興味・学習スタイルを設定
                estimated_interests = estimate_interests_from_username(username)
                estimated_learning_style = "実践的学習者"
                
                # 実在するアカウントとマッチング（推定設定で）
                matches = get_matching_accounts(estimated_interests, estimated_learning_style, max_matches=5)
                logger.info(f"Fallback matching for {username}: {len(matches)} matches found")
                
                analysis_result = {
                    "username": username,
                    "display_name": f"@{username}",
                    "followers_count": "取得中",
                    "following_count": "取得中", 
                    "tweets_count": "取得中",
                    "account_created": "情報取得中",
                    "verified": False,
                    "profile_image_url": "",
                    "description": "",
                    "location": "",
                    "analysis": {
                        "interests": estimated_interests,
                        "learning_style": estimated_learning_style,
                        "personality_traits": ["学習意欲", "向上心", "探究心"],
                        "study_preferences": ["オンライン学習", "自主学習", "コミュニティ学習"],
                        "activity_level": "推定中",
                        "engagement_pattern": "推定中"
                    },
                    "matches": matches,
                    "api_note": "Twitter APIの制限により、一時的に詳細情報を取得できません。マッチング結果は推定に基づいています。"
                }
            
            logger.info(f"Analysis completed for user: {username}")
            
            return jsonify({
                "success": True,
                "message": "分析が完了しました",
                "analysis": analysis_result
            })
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return jsonify({"success": False, "error": "分析中にエラーが発生しました"}), 500
    
    @app.route('/test-fix')
    def test_fix():
        """修正結果確認ページ"""
        return render_template('test_fix.html', title='修正結果確認 - TOU Connect')
    
    @app.route('/about')
    def about():
        """アバウトページ"""
        return render_template('about.html', title='About - TOU Connect')
    
    @app.route('/contact')
    def contact():
        """コンタクトページ"""
        return render_template('contact.html', title='Contact - TOU Connect')
    
    @app.route('/matching')
    def matching():
        """学友マッチングページ"""
        return render_template('matching.html', title='学友マッチング - TOU Connect')
    
    @app.route('/resources')
    def resources():
        """学習リソースページ"""
        return render_template('resources.html', title='学習リソース - TOU Connect')
    
    @app.route('/monitoring')
    def monitoring():
        """システム監視ページ"""
        return render_template('monitoring_dashboard.html', title='システム監視 - TOU Connect')
    
    @app.route('/privacy')
    def privacy():
        """プライバシーポリシーページ"""
        return render_template('privacy.html', title='プライバシーポリシー - TOU Connect')
    
    @app.route('/terms')
    def terms():
        """利用規約ページ"""
        return render_template('terms.html', title='利用規約 - TOU Connect')
    
    @app.errorhandler(404)
    def not_found_error(error):
        """404エラーハンドラー"""
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500エラーハンドラー"""
        logger.error(f"Internal server error: {error}")
        return render_template('500.html'), 500
    
    logger.info("Simple TOU Connect app created successfully")
    return app

# アプリケーションインスタンス作成
app = create_simple_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"Starting TOU Connect on {host}:{port}")
    app.run(host=host, port=port, debug=app.config['DEBUG'])
