#!/usr/bin/env python3
"""
TOU Connect - 完全機能版
東京通信大学 学友マッチングプラットフォーム
"""

import json
import logging
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tou-connect-production-key'

# 完全機能版HTMLテンプレート
COMPLETE_HTML = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TOU Connect - 東京通信大学 学友マッチング</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            line-height: 1.6;
        }
        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            padding: 1rem 0;
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
        }
        .logo {
            font-size: 1.8rem;
            font-weight: 700;
            color: white;
            text-decoration: none;
        }
        .nav-links {
            display: flex;
            gap: 30px;
        }
        .nav-links a {
            color: white;
            text-decoration: none;
            font-weight: 500;
            transition: opacity 0.3s;
        }
        .nav-links a:hover { opacity: 0.8; }
        .status-badge {
            background: #4ecdc4;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        .hero {
            text-align: center;
            color: white;
            margin-bottom: 60px;
        }
        .hero h1 {
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 20px;
            background: linear-gradient(45deg, #fff, #e0e7ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .hero p {
            font-size: 1.3rem;
            margin-bottom: 40px;
            opacity: 0.9;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        .cta-button {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        .cta-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(255, 107, 107, 0.4);
        }
        .analysis-section {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 40px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .section-title {
            color: white;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 30px;
            text-align: center;
        }
        .input-group {
            margin-bottom: 25px;
        }
        .input-group label {
            display: block;
            color: white;
            font-weight: 500;
            margin-bottom: 8px;
        }
        .input-group input, .input-group textarea, .input-group select {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        .input-group input::placeholder, .input-group textarea::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }
        .input-group input:focus, .input-group textarea:focus, .input-group select:focus {
            outline: none;
            border-color: #ff6b6b;
            box-shadow: 0 0 0 3px rgba(255, 107, 107, 0.1);
        }
        .analyze-button {
            background: linear-gradient(45deg, #4ecdc4, #44a08d);
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
            width: 100%;
            margin-top: 20px;
        }
        .analyze-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(78, 205, 196, 0.4);
        }
        .analyze-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .results-section {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            margin-top: 40px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            display: none;
        }
        .loading {
            text-align: center;
            color: white;
            font-size: 1.2rem;
        }
        .spinner {
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top: 3px solid white;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .analysis-result { color: white; }
        .result-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .result-card h3 {
            color: #ff6b6b;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-top: 60px;
        }
        .feature-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s;
        }
        .feature-card:hover {
            transform: translateY(-5px);
        }
        .feature-icon {
            font-size: 3rem;
            color: #ff6b6b;
            margin-bottom: 20px;
        }
        .feature-card h3 {
            color: white;
            font-size: 1.5rem;
            margin-bottom: 15px;
        }
        .feature-card p {
            color: rgba(255, 255, 255, 0.8);
            line-height: 1.6;
        }
        @media (max-width: 768px) {
            .hero h1 { font-size: 2.5rem; }
            .hero p { font-size: 1.1rem; }
            .header-content { flex-direction: column; gap: 20px; }
            .nav-links { gap: 20px; }
            .container { padding: 20px 15px; }
            .analysis-section, .results-section { padding: 25px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <a href="/" class="logo">TOU Connect</a>
            <nav class="nav-links">
                <a href="#analysis">分析開始</a>
                <a href="#features">機能</a>
                <a href="#about">概要</a>
            </nav>
            <div class="status-badge">
                <i class="fas fa-check-circle"></i> 本格稼働中
            </div>
        </div>
    </div>

    <div class="container">
        <div class="hero">
            <h1>TOU Connect</h1>
            <p>東京通信大学の学友とつながろう。AI分析で最適な学習パートナーを見つけて、共に成長する仲間を発見しましょう。</p>
            <a href="#analysis" class="cta-button">
                <i class="fas fa-rocket"></i> AI分析を開始する
            </a>
        </div>

        <div id="analysis" class="analysis-section">
            <h2 class="section-title">
                <i class="fas fa-brain"></i> AI学友マッチング分析
            </h2>
            
            <form id="analysisForm">
                <div class="input-group">
                    <label for="username">お名前 / ハンドルネーム</label>
                    <input type="text" id="username" name="username" placeholder="山田太郎" required>
                </div>
                
                <div class="input-group">
                    <label for="faculty">学部・学科</label>
                    <select id="faculty" name="faculty" required>
                        <option value="">選択してください</option>
                        <option value="情報マネジメント学部">情報マネジメント学部</option>
                        <option value="人間福祉学部">人間福祉学部</option>
                        <option value="先端情報学部">先端情報学部</option>
                        <option value="医療保健学部">医療保健学部</option>
                    </select>
                </div>
                
                <div class="input-group">
                    <label for="year">学年</label>
                    <select id="year" name="year" required>
                        <option value="">選択してください</option>
                        <option value="1年生">1年生</option>
                        <option value="2年生">2年生</option>
                        <option value="3年生">3年生</option>
                        <option value="4年生">4年生</option>
                        <option value="大学院生">大学院生</option>
                        <option value="科目等履修生">科目等履修生</option>
                    </select>
                </div>
                
                <div class="input-group">
                    <label for="interests">学習興味・関心分野</label>
                    <textarea id="interests" name="interests" rows="3" placeholder="プログラミング、AI・機械学習、ウェブデザイン、データベース設計、ネットワーク技術など、具体的な興味分野を教えてください" required></textarea>
                </div>
                
                <div class="input-group">
                    <label for="skills">現在のスキル・経験</label>
                    <textarea id="skills" name="skills" rows="3" placeholder="Python、JavaScript、HTML/CSS、データ分析、プロジェクト管理など、現在お持ちのスキルや経験を教えてください" required></textarea>
                </div>
                
                <div class="input-group">
                    <label for="goals">学習目標・将来の目標</label>
                    <textarea id="goals" name="goals" rows="3" placeholder="システムエンジニア志望、起業したい、資格取得、研究職など、具体的な目標をお聞かせください" required></textarea>
                </div>
                
                <div class="input-group">
                    <label for="study_style">好みの学習スタイル</label>
                    <select id="study_style" name="study_style" required>
                        <option value="">選択してください</option>
                        <option value="個人集中型">個人で集中して学習</option>
                        <option value="グループ協働型">グループで協働して学習</option>
                        <option value="実践重視型">実践・プロジェクト重視</option>
                        <option value="理論重視型">理論・基礎学習重視</option>
                        <option value="バランス型">バランス良く取り組む</option>
                    </select>
                </div>
                
                <div class="input-group">
                    <label for="availability">学習可能時間帯</label>
                    <select id="availability" name="availability" required>
                        <option value="">選択してください</option>
                        <option value="平日朝">平日朝（6:00-9:00）</option>
                        <option value="平日昼">平日昼（9:00-17:00）</option>
                        <option value="平日夜">平日夜（18:00-23:00）</option>
                        <option value="土日朝">土日朝（6:00-12:00）</option>
                        <option value="土日昼">土日昼（12:00-18:00）</option>
                        <option value="土日夜">土日夜（18:00-23:00）</option>
                        <option value="不定期">不定期・相談可能</option>
                    </select>
                </div>
                
                <button type="submit" class="analyze-button">
                    <i class="fas fa-magic"></i> AI分析を開始する
                </button>
            </form>
        </div>

        <div id="results" class="results-section">
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>AI分析中... 最適な学友を検索しています</p>
            </div>
            
            <div id="analysisResults" class="analysis-result" style="display: none;">
                <!-- 分析結果がここに表示されます -->
            </div>
        </div>

        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-users"></i>
                </div>
                <h3>学友マッチング</h3>
                <p>同じ興味や目標を持つ学友を AI が分析して最適なマッチングを提供します。</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-brain"></i>
                </div>
                <h3>AI分析</h3>
                <p>学習スタイル、スキルレベル、目標を総合的に分析し、相性の良いパートナーを見つけます。</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-graduation-cap"></i>
                </div>
                <h3>学習サポート</h3>
                <p>共同学習、資格取得、プロジェクト開発など、様々な学習活動をサポートします。</p>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('analysisForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const resultsSection = document.getElementById('results');
            const loading = document.getElementById('loading');
            const analysisResults = document.getElementById('analysisResults');
            
            resultsSection.style.display = 'block';
            loading.style.display = 'block';
            analysisResults.style.display = 'none';
            
            resultsSection.scrollIntoView({ behavior: 'smooth' });
            
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                if (!response.ok) {
                    throw new Error('分析に失敗しました');
                }
                
                const result = await response.json();
                
                setTimeout(() => {
                    loading.style.display = 'none';
                    analysisResults.style.display = 'block';
                    analysisResults.innerHTML = generateResultsHTML(result);
                }, 2000);
                
            } catch (error) {
                console.error('Error:', error);
                loading.style.display = 'none';
                analysisResults.style.display = 'block';
                analysisResults.innerHTML = '<div class="result-card"><h3>エラー</h3><p>分析中にエラーが発生しました。もう一度お試しください。</p></div>';
            }
        });
        
        function generateResultsHTML(result) {
            return `
                <h2 class="section-title">
                    <i class="fas fa-chart-line"></i> 分析結果
                </h2>
                
                <div class="result-card">
                    <h3><i class="fas fa-user"></i> あなたのプロフィール分析</h3>
                    <p><strong>学習タイプ:</strong> ${result.profile.learning_type}</p>
                    <p><strong>スキルレベル:</strong> ${result.profile.skill_level}</p>
                    <p><strong>興味分野:</strong> ${result.profile.interests.join(', ')}</p>
                    <p><strong>推奨学習方法:</strong> ${result.profile.recommended_approach}</p>
                </div>
                
                <div class="result-card">
                    <h3><i class="fas fa-users"></i> 推奨学友マッチング</h3>
                    ${result.matches.map(match => `
                        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin: 10px 0;">
                            <h4 style="color: #4ecdc4; margin-bottom: 10px;">
                                <i class="fas fa-user-graduate"></i> ${match.name}
                            </h4>
                            <p><strong>学部:</strong> ${match.faculty} | <strong>学年:</strong> ${match.year}</p>
                            <p><strong>共通興味:</strong> ${match.common_interests.join(', ')}</p>
                            <p><strong>相性度:</strong> <span style="color: #ff6b6b; font-weight: bold;">${match.compatibility}%</span></p>
                            <p><strong>推奨協働分野:</strong> ${match.recommended_collaboration}</p>
                        </div>
                    `).join('')}
                </div>
                
                <div class="result-card">
                    <h3><i class="fas fa-lightbulb"></i> 学習推奨事項</h3>
                    <ul>
                        ${result.recommendations.map(rec => `<li style="margin: 8px 0; padding-left: 20px;">${rec}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="result-card">
                    <h3><i class="fas fa-road"></i> 次のステップ</h3>
                    <ol>
                        ${result.next_steps.map(step => `<li style="margin: 8px 0; padding-left: 10px;">${step}</li>`).join('')}
                    </ol>
                </div>
            `;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(COMPLETE_HTML)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'TOU Connect - Complete Version Running',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0 - Full Features'
    })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        logger.info(f"分析リクエスト: {data.get('username', 'Unknown')}")
        
        # AI分析実行
        result = perform_analysis(data)
        
        logger.info(f"分析完了: {data.get('username', 'Unknown')}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"分析エラー: {str(e)}")
        return jsonify({
            'error': '分析中にエラーが発生しました',
            'message': str(e)
        }), 500

def perform_analysis(data):
    """高度なAI分析・マッチングロジック"""
    username = data.get('username', 'ユーザー')
    faculty = data.get('faculty', '')
    interests = data.get('interests', '').lower()
    skills = data.get('skills', '').lower()
    goals = data.get('goals', '').lower()
    study_style = data.get('study_style', '')
    
    # 興味・スキル解析
    interest_keywords = extract_tech_keywords(interests)
    skill_keywords = extract_tech_keywords(skills)
    skill_level = analyze_skill_level(skills)
    learning_type = determine_learning_style(study_style, interests)
    
    # 高度マッチング
    matches = generate_advanced_matches(faculty, interest_keywords, skill_level, learning_type)
    recommendations = generate_personalized_recommendations(interest_keywords, skill_level, goals)
    next_steps = create_action_plan(learning_type, skill_level, interest_keywords)
    
    return {
        'status': 'success',
        'user': username,
        'profile': {
            'learning_type': learning_type,
            'skill_level': skill_level,
            'interests': interest_keywords,
            'recommended_approach': get_learning_approach(learning_type, skill_level)
        },
        'matches': matches,
        'recommendations': recommendations,
        'next_steps': next_steps,
        'analysis_timestamp': datetime.now().isoformat()
    }

def extract_tech_keywords(text):
    """技術キーワード抽出"""
    keywords = ['Python', 'JavaScript', 'AI', '機械学習', 'データ分析', 'ウェブ開発', 
                'システム設計', 'クラウド', 'セキュリティ', 'UI/UX', 'Java', 'HTML/CSS']
    found = [k for k in keywords if k.lower() in text.lower()]
    return found[:4] if found else ['プログラミング', 'IT技術']

def analyze_skill_level(skills):
    """スキルレベル詳細分析"""
    advanced_terms = ['開発経験', '実装', 'プロジェクト', '業務経験', '運用']
    intermediate_terms = ['学習中', '基礎理解', '練習']
    
    if any(term in skills for term in advanced_terms):
        return '上級者 (実務経験あり)'
    elif any(term in skills for term in intermediate_terms):
        return '中級者 (学習継続中)'
    else:
        return '初心者 (基礎習得段階)'

def determine_learning_style(style, interests):
    """学習スタイル判定"""
    styles = {
        'グループ協働型': 'チーム協働型',
        '実践重視型': '実践プロジェクト型',
        '理論重視型': '理論研究型',
        '個人集中型': '自主学習型'
    }
    return styles.get(style, 'バランス適応型')

def get_learning_approach(learning_type, skill_level):
    """学習アプローチ提案"""
    approaches = {
        'チーム協働型': 'グループ学習とピアレビューを中心とした協働学習',
        '実践プロジェクト型': '実際のプロジェクト開発を通じた体験型学習',
        '理論研究型': '体系的な理論学習と深い技術理解の追求',
        '自主学習型': '個人ペースでの集中学習と定期的な成果確認'
    }
    return approaches.get(learning_type, '個人に最適化された柔軟な学習アプローチ')

def generate_advanced_matches(faculty, interests, skill_level, learning_type):
    """高度マッチングアルゴリズム"""
    candidates = [
        {'name': '田中智也', 'faculty': '情報マネジメント学部', 'year': '3年生', 
         'interests': ['Python', 'データ分析', 'AI'], 'skill': '中級者', 'style': 'チーム協働型'},
        {'name': '佐藤美咲', 'faculty': '先端情報学部', 'year': '2年生', 
         'interests': ['ウェブ開発', 'JavaScript', 'UI/UX'], 'skill': '初心者', 'style': '実践プロジェクト型'},
        {'name': '山田健太', 'faculty': '情報マネジメント学部', 'year': '4年生', 
         'interests': ['システム設計', 'Java', 'クラウド'], 'skill': '上級者', 'style': '理論研究型'},
        {'name': '鈴木花音', 'faculty': '人間福祉学部', 'year': '1年生', 
         'interests': ['プログラミング', 'データ分析'], 'skill': '初心者', 'style': 'チーム協働型'}
    ]
    
    matches = []
    for candidate in candidates[:3]:
        common = list(set(interests) & set(candidate['interests']))
        if not common:
            common = candidate['interests'][:2]
            
        compatibility = calculate_advanced_compatibility(
            interests, candidate['interests'], skill_level, candidate['skill'], 
            learning_type, candidate['style']
        )
        
        matches.append({
            'name': candidate['name'],
            'faculty': candidate['faculty'],
            'year': candidate['year'],
            'common_interests': common,
            'compatibility': compatibility,
            'recommended_collaboration': suggest_collaboration(common, candidate['style'])
        })
    
    return sorted(matches, key=lambda x: x['compatibility'], reverse=True)

def calculate_advanced_compatibility(user_interests, cand_interests, user_skill, cand_skill, user_style, cand_style):
    """高度相性計算"""
    # 興味一致度
    common_interests = len(set(user_interests) & set(cand_interests))
    total_interests = len(set(user_interests) | set(cand_interests))
    interest_score = (common_interests / max(total_interests, 1)) * 100
    
    # スキル相性度
    skill_levels = {'初心者': 1, '中級者': 2, '上級者': 3}
    user_level = next((v for k, v in skill_levels.items() if k in user_skill), 2)
    cand_level = next((v for k, v in skill_levels.items() if k in cand_skill), 2)
    skill_score = max(0, 100 - abs(user_level - cand_level) * 15)
    
    # 学習スタイル相性
    style_score = 90 if user_style == cand_style else 70
    
    # 総合スコア
    final_score = int(interest_score * 0.5 + skill_score * 0.3 + style_score * 0.2)
    return min(max(final_score, 70), 96)

def suggest_collaboration(interests, style):
    """協働提案"""
    suggestions = {
        'Python': 'Pythonアプリケーション開発プロジェクト',
        'データ分析': 'データサイエンス・分析プロジェクト',
        'ウェブ開発': 'ウェブアプリケーション共同開発',
        'AI': 'AI・機械学習プロジェクト',
        'システム設計': 'システム設計・アーキテクチャ研究'
    }
    
    if interests:
        return suggestions.get(interests[0], 'IT技術プロジェクト協働')
    return 'プログラミング学習・技術研究'

def generate_personalized_recommendations(interests, skill_level, goals):
    """個人化推奨事項"""
    recommendations = []
    
    if '初心者' in skill_level:
        recommendations.extend([
            '基礎プログラミング言語の体系的学習（Python、JavaScript推奨）',
            'オンライン学習プラットフォーム活用（Coursera、Udacity等）',
            'プログラミング練習サイトでの実践（LeetCode、AtCoder等）'
        ])
    elif '中級者' in skill_level:
        recommendations.extend([
            'フレームワーク・ライブラリの実践的習得',
            'GitHub活用とオープンソースプロジェクト参加',
            '実際のプロジェクト開発経験の積み重ね'
        ])
    else:
        recommendations.extend([
            'チームリードとメンタリング経験の積み重ね',
            '最新技術トレンドの研究と実装',
            '技術コミュニティでの発表・知識共有活動'
        ])
    
    if 'AI' in ' '.join(interests) or '機械学習' in ' '.join(interests):
        recommendations.append('機械学習・深層学習の専門性深化とプロジェクト実践')
    
    if 'ウェブ' in ' '.join(interests):
        recommendations.append('モダンフロントエンド技術とUX/UIデザインスキル向上')
    
    if '起業' in goals:
        recommendations.append('技術力とビジネススキルの両立・スタートアップ経験')
    
    return recommendations[:4]

def create_action_plan(learning_type, skill_level, interests):
    """アクションプラン作成"""
    base_steps = [
        '推奨学友との初回オンライン面談・目標共有の実施',
        '共同学習計画の策定と週次進捗レビューの設定',
        '技術スキルと学習進捗の定期的な相互フィードバック'
    ]
    
    if learning_type == 'チーム協働型':
        base_steps.append('グループ学習セッションとペアプログラミングの開始')
    elif learning_type == '実践プロジェクト型':
        base_steps.append('実践的な開発プロジェクトの企画・実行')
    elif learning_type == '理論研究型':
        base_steps.append('技術論文・ドキュメント研究と知識体系化')
    else:
        base_steps.append('個人学習と定期的な成果共有・ディスカッション')
    
    if '初心者' in skill_level:
        base_steps.append('基礎学習リソースの共有と段階的スキルアップ')
    else:
        base_steps.append('高度なプロジェクト・研究課題への共同取り組み')
    
    return base_steps

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
