# リアルタイム申請サポート

## 🎯 申請フォーム記入ガイド

### 基本情報入力

#### Personal Information
- **Name**: あなたの実名を入力
- **Country**: Japan
- **Email**: あなたのメールアドレス

#### Use Case Selection
**Academic research** を選択してください

### プロジェクト詳細入力

#### 1. Project Name
```
TOU Connect - Student Networking Platform
```

#### 2. Project Description
以下をコピー&ペーストしてください：

```
I am developing an educational platform to help students at Tokyo Online University (TOU) connect with each other and build academic communities. As a distance learning institution, TOU students often struggle to form meaningful connections with their peers due to the lack of physical campus interactions.

This platform addresses a significant challenge in distance education by helping students overcome isolation and build meaningful academic relationships. The goal is to improve learning outcomes, increase student engagement, and enhance the overall university experience for distance learning students.

The project is purely educational and non-commercial, aimed at supporting the academic success and social well-being of university students in a digital learning environment.
```

#### 3. How will you use Twitter data?
以下をコピー&ペーストしてください：

```
1. Profile Analysis: Analyze public Twitter profiles to identify TOU-related accounts and academic interests
2. Interest Extraction: Extract academic interests, study fields, and learning patterns from public tweets
3. Community Building: Help students find study partners with similar academic interests and goals
4. Academic Support: Facilitate collaboration on coursework, projects, and study groups
5. Networking Facilitation: Connect students based on complementary skills and shared academic pursuits

Data Usage and Privacy:
- Only public profile information and tweets will be accessed
- No private messages, DMs, or protected content will be accessed
- Data will be used solely for academic networking and educational purposes
- All data handling will comply with privacy regulations and Twitter's terms of service
- Personal information will be anonymized and aggregated for analysis
- No data will be sold, shared with third parties, or used for commercial purposes

Technical Implementation:
- Using Twitter API v2 Basic tier (respecting 10,000 tweets/month limit)
- Implementing proper rate limiting and caching mechanisms
- Storing only aggregated, anonymized insights for matching purposes
- Using AI analysis to extract academic interests and compatibility
- No automated posting or engagement - read-only access only

Expected monthly API usage: 5,000-8,000 tweets
Target user base: Tokyo Online University students (approximately 500-1000 users)
Data retention: Minimal, only for matching purposes
```

#### 4. Will you make Twitter content available to a government entity?
```
No
```

#### 5. Will you display Twitter content off Twitter?
```
Only aggregated, anonymized insights for educational matching purposes. No individual tweets or personal information will be displayed publicly.
```

## 📋 申請チェックリスト

申請前に以下を確認してください：

- [ ] X Developer Portal にログイン済み
- [ ] 基本情報（名前、国、メール）入力済み
- [ ] Use case で "Academic research" を選択済み
- [ ] プロジェクト名を入力済み
- [ ] プロジェクト説明をコピー&ペースト済み
- [ ] データ利用方針をコピー&ペースト済み
- [ ] 政府機関への提供で "No" を選択済み
- [ ] Twitter外での表示について回答済み
- [ ] 内容を最終確認済み

## 🎉 申請完了後

申請送信後：
1. 確認メールが届きます
2. 1-7営業日で審査結果通知
3. 承認後、Bearer Token取得
4. .env ファイルに設定
5. 実データでのテスト開始！

## 📞 申請中のサポート

申請フォーム記入中に不明な点があれば、いつでも質問してください。
一緒に進めましょう！