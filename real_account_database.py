#!/usr/bin/env python3
"""
実在のアカウントデータベース - 教育・学習関連のTwitterアカウント
"""

# 実在する教育・学習関連のTwitterアカウント（公開情報）
REAL_EDUCATION_ACCOUNTS = [
    {
        "username": "edutechzine",
        "display_name": "EdTechZine",
        "category": "教育メディア",
        "interests": ["教育技術", "EdTech", "オンライン学習", "デジタル教育"],
        "learning_style": "情報収集型",
        "personality_traits": ["探究心", "情報発信", "専門性"],
        "description": "教育×ITの情報メディア"
    },
    {
        "username": "khan_academy",
        "display_name": "Khan Academy",
        "category": "オンライン教育",
        "interests": ["数学", "科学", "プログラミング", "無料教育"],
        "learning_style": "実践的学習者",
        "personality_traits": ["支援的", "体系的", "包括的"],
        "description": "世界中に無料で質の高い教育を提供"
    },
    {
        "username": "coursera",
        "display_name": "Coursera",
        "category": "オンライン学習プラットフォーム",
        "interests": ["大学レベル教育", "専門スキル", "認定証", "キャリア開発"],
        "learning_style": "構造化学習者",
        "personality_traits": ["目標志向", "学習意欲", "継続性"],
        "description": "世界の大学・企業と連携したオンライン学習"
    },
    {
        "username": "udemy",
        "display_name": "Udemy",
        "category": "スキル学習",
        "interests": ["プログラミング", "ビジネススキル", "クリエイティブ", "実用的スキル"],
        "learning_style": "実践的学習者",
        "personality_traits": ["実用性重視", "効率性", "多様性"],
        "description": "オンライン学習でスキルアップ"
    },
    {
        "username": "edx",
        "display_name": "edX",
        "category": "高等教育",
        "interests": ["大学教育", "研究", "学術的内容", "専門知識"],
        "learning_style": "学術的学習者",
        "personality_traits": ["学術志向", "深い理解", "研究的"],
        "description": "世界トップ大学の無料オンラインコース"
    },
    {
        "username": "duolingo",
        "display_name": "Duolingo",
        "category": "言語学習",
        "interests": ["語学", "多言語", "ゲーミフィケーション", "日常学習"],
        "learning_style": "継続的学習者",
        "personality_traits": ["継続性", "楽しさ重視", "コミュニティ志向"],
        "description": "楽しく続けられる語学学習アプリ"
    },
    {
        "username": "codecademy",
        "display_name": "Codecademy",
        "category": "プログラミング教育",
        "interests": ["プログラミング", "ウェブ開発", "データサイエンス", "テクノロジー"],
        "learning_style": "実践的学習者",
        "personality_traits": ["技術志向", "実践的", "問題解決型"],
        "description": "インタラクティブなプログラミング学習"
    },
    {
        "username": "ted",
        "display_name": "TED",
        "category": "知識共有",
        "interests": ["アイデア", "イノベーション", "講演", "知識共有"],
        "learning_style": "視覚的学習者",
        "personality_traits": ["好奇心", "インスピレーション重視", "多様性"],
        "description": "Ideas worth spreading"
    },
    {
        "username": "mitocw",
        "display_name": "MIT OpenCourseWare",
        "category": "高等教育",
        "interests": ["科学", "工学", "数学", "研究"],
        "learning_style": "学術的学習者",
        "personality_traits": ["学術志向", "深い理解", "体系的"],
        "description": "MITの授業を無料で公開"
    },
    {
        "username": "programming_jp",
        "display_name": "プログラミング学習",
        "category": "日本のプログラミング",
        "interests": ["プログラミング", "開発", "技術情報", "日本語"],
        "learning_style": "実践的学習者",
        "personality_traits": ["技術志向", "日本語重視", "コミュニティ"],
        "description": "日本語でプログラミングを学ぼう"
    },
    {
        "username": "techacademy_jp",
        "display_name": "TechAcademy",
        "category": "日本のプログラミング教育",
        "interests": ["プログラミング", "ウェブ開発", "転職支援", "実務スキル"],
        "learning_style": "実践的学習者",
        "personality_traits": ["キャリア重視", "実践的", "効率性"],
        "description": "オンラインプログラミングスクール"
    },
    {
        "username": "paiza_official",
        "display_name": "paiza",
        "category": "プログラミング学習・転職",
        "interests": ["プログラミング", "転職", "スキルチェック", "ゲーミフィケーション"],
        "learning_style": "実践的学習者",
        "personality_traits": ["成長志向", "競争心", "効率性"],
        "description": "プログラミング学習・転職サービス"
    }
]

# 日本の大学・教育機関の公式アカウント（参考）
JAPANESE_UNIVERSITY_ACCOUNTS = [
    {
        "username": "UTokyo_News",
        "display_name": "東京大学",
        "category": "国立大学",
        "interests": ["研究", "学術", "最新情報", "大学生活"],
        "learning_style": "学術的学習者",
        "personality_traits": ["学術志向", "研究重視", "伝統的"],
        "description": "東京大学の公式情報"
    },
    {
        "username": "waseda_univ",
        "display_name": "早稲田大学",
        "category": "私立大学",
        "interests": ["大学生活", "イベント", "学生活動", "教育"],
        "learning_style": "活動的学習者",
        "personality_traits": ["活発", "伝統的", "多様性"],
        "description": "早稲田大学公式アカウント"
    },
    {
        "username": "keio_univ",
        "display_name": "慶應義塾",
        "category": "私立大学",
        "interests": ["教育", "研究", "福澤諭吉", "実学"],
        "learning_style": "実践的学習者",
        "personality_traits": ["実学重視", "伝統的", "国際的"],
        "description": "慶應義塾公式アカウント"
    }
]

def get_matching_accounts(user_interests, user_learning_style, max_matches=5):
    """
    ユーザーの興味と学習スタイルに基づいて、実在するアカウントからマッチングを行う
    """
    all_accounts = REAL_EDUCATION_ACCOUNTS + JAPANESE_UNIVERSITY_ACCOUNTS
    matches = []
    
    for account in all_accounts:
        score = calculate_compatibility_score(
            user_interests, 
            user_learning_style,
            account["interests"],
            account["learning_style"]
        )
        
        if score > 30:  # しきい値を下げて、より多くのマッチング候補を表示
            matches.append({
                "username": account["username"],
                "display_name": account["display_name"],
                "compatibility_score": score,
                "match_reasons": get_match_reasons(user_interests, account["interests"]),
                "category": account["category"],
                "description": account["description"]
            })
    
    # スコア順にソートして上位を返す
    matches.sort(key=lambda x: x["compatibility_score"], reverse=True)
    return matches[:max_matches]

def calculate_compatibility_score(user_interests, user_learning_style, account_interests, account_learning_style):
    """互換性スコアを計算"""
    score = 0
    
    # 興味の一致度 (60%)
    user_interests_lower = [interest.lower() for interest in user_interests]
    account_interests_lower = [interest.lower() for interest in account_interests]
    
    exact_matches = len(set(user_interests_lower) & set(account_interests_lower))
    partial_matches = 0
    
    # 部分マッチングの検出
    for user_interest in user_interests_lower:
        for account_interest in account_interests_lower:
            if user_interest in account_interest or account_interest in user_interest:
                if user_interest not in set(user_interests_lower) & set(account_interests_lower):
                    partial_matches += 0.5
    
    max_interests = max(len(user_interests), len(account_interests))
    if max_interests > 0:
        interest_score = ((exact_matches + partial_matches) / max_interests) * 60
        score += interest_score
    
    # 学習スタイルの一致度 (40%)
    if user_learning_style == account_learning_style:
        score += 40
    elif user_learning_style in account_learning_style or account_learning_style in user_learning_style:
        score += 25
    elif "実践的" in user_learning_style and "実践的" in account_learning_style:
        score += 20
    elif "学術的" in user_learning_style and "学術的" in account_learning_style:
        score += 20
    
    return min(int(score), 95)  # 最大95%に制限

def get_match_reasons(user_interests, account_interests):
    """マッチング理由を生成"""
    common_interests = list(set(user_interests) & set(account_interests))
    reasons = []
    
    if common_interests:
        if len(common_interests) == 1:
            reasons.append(f"共通の興味: {common_interests[0]}")
        else:
            reasons.append(f"共通の興味: {', '.join(common_interests[:2])}")
    
    reasons.append("教育・学習関連")
    reasons.append("信頼できる情報源")
    
    return reasons[:3]  # 最大3つまで

if __name__ == "__main__":
    # テスト
    test_interests = ["プログラミング", "テクノロジー", "教育"]
    test_learning_style = "実践的学習者"
    
    matches = get_matching_accounts(test_interests, test_learning_style)
    print("マッチング結果:")
    for match in matches:
        print(f"- @{match['username']}: {match['compatibility_score']}% ({', '.join(match['match_reasons'])})")
