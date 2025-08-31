# Twitter API申請 ステップバイステップガイド

## 🎯 申請フォーム記入手順

### 1. X Developer Portal アクセス
- URL: https://developer.twitter.com/en/portal/dashboard
- 「Sign up for Free Account」をクリック
- 既存のXアカウント（@ike3don3）でログイン

### 2. 基本情報入力

#### Personal Information
- **Name**: あなたの実名
- **Country**: Japan
- **Email**: あなたのメールアドレス

#### Use Case Selection
- **Academic research** を選択

### 3. 詳細説明入力

#### Project Name
```
TOU Connect - Student Networking Platform
```

#### Project Description (英語で記入)
```
I am developing an educational platform to help students at Tokyo Online University (TOU) connect with each other and build academic communities. As a distance learning institution, TOU students often struggle to form meaningful connections with their peers due to the lack of physical campus interactions.

This platform addresses a significant challenge in distance education by helping students overcome isolation and build meaningful academic relationships. The goal is to improve learning outcomes, increase student engagement, and enhance the overall university experience for distance learning students.
```

#### How will you use Twitter data? (英語で記入)
```
1. Profile Analysis: Analyze public Twitter profiles to identify TOU-related accounts and academic interests
2. Interest Extraction: Extract academic interests, study fields, and learning patterns from public tweets  
3. Community Building: Help students find study partners with similar academic interests and goals
4. Academic Support: Facilitate collaboration on coursework, projects, and study groups
5. Networking Facilitation: Connect students based on complementary skills and shared academic pursuits

Data Usage:
- Only public profile information and tweets will be accessed
- No private messages, DMs, or protected content will be accessed
- Data will be used solely for academic networking and educational purposes
- Personal information will be anonymized and aggregated for analysis
- No data will be sold, shared with third parties, or used for commercial purposes
```

#### Will you make Twitter content available to a government entity?
```
No
```

#### Will you display Twitter content off Twitter?
```
Yes, but only aggregated and anonymized insights for educational matching purposes. No individual tweets or personal information will be displayed.
```

### 4. 技術的詳細

#### Expected API Usage
```
- Monthly tweet retrieval: 5,000-8,000 tweets
- API endpoints: User lookup, Tweet lookup (read-only)
- Rate limiting: Respecting all API limits
- Caching: Implementing proper caching to minimize requests
```

#### Data Retention
```
Minimal data retention - only aggregated insights for matching purposes. No personal tweets or profile information stored long-term.
```

### 5. 申請送信後

#### 承認までの期間
- 通常: 1-7営業日
- 学術目的: 比較的早期承認の傾向

#### 承認通知
- メールで通知が届きます
- Developer Portal でステータス確認可能

#### 承認後の作業
1. Developer Portal にログイン
2. 「Projects & Apps」→「Create App」
3. アプリ名: `TOU Connect`
4. 「Keys and Tokens」タブ
5. **Bearer Token** をコピー
6. `.env` ファイルに設定:
   ```
   TWITTER_BEARER_TOKEN=your_actual_bearer_token_here
   ```

### 6. 動作確認
```bash
python api_status_tracker.py
```

## 🚨 申請のコツ

### ✅ 成功のポイント
- 教育目的であることを明確に記載
- プライバシー保護への配慮を強調
- 具体的な社会的課題解決を説明
- 非営利・学術目的であることを明記

### ❌ 避けるべき表現
- 「データ収集」「マーケティング」
- 「商用利用」「収益化」
- 曖昧な用途説明
- プライバシーへの配慮不足

## 📞 サポート

### 申請で困った場合
1. API_APPLICATION_GUIDE.md を参照
2. 申請却下時は理由を確認して再申請
3. 開発は現在のモックデータで継続可能

### 技術的な問題
- check_api_setup.py で設定確認
- api_status_tracker.py で状況追跡