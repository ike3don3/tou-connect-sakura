# Twitter API v2 申請ガイド（詳細版）

## 🚀 申請手順

### Step 1: X Developer Portal アクセス
1. https://developer.twitter.com/en/portal/dashboard にアクセス
2. 「Sign up for Free Account」をクリック
3. 既存のXアカウントでログイン

### Step 2: 申請フォーム記入

#### 基本情報
- **Name**: あなたの実名
- **Country**: Japan
- **Use case**: Academic research

#### 詳細な使用目的（英語で記載）
```
Project Title: TOU Connect - Student Networking Platform for Tokyo Online University

Project Description:
I am developing an educational platform to help students at Tokyo Online University (TOU) connect with each other and build academic communities. As a distance learning institution, TOU students often struggle to form meaningful connections with their peers.

Specific Use Cases:
1. Profile Analysis: Analyze public Twitter profiles to identify TOU-related accounts
2. Interest Extraction: Extract academic interests and study fields from public tweets
3. Community Building: Help students find study partners with similar interests
4. Academic Support: Facilitate collaboration on coursework and projects

Data Usage:
- Only public profile information and tweets will be accessed
- No private or sensitive data will be collected
- Data will be used solely for academic networking purposes
- All data handling will comply with privacy regulations

Technical Implementation:
- Using Twitter API v2 Basic tier (10,000 tweets/month limit)
- Implementing proper rate limiting and caching
- Storing only aggregated, anonymized insights
- No resale or commercial use of data

Educational Impact:
This platform addresses a real challenge in distance education by helping students overcome isolation and build meaningful academic relationships, ultimately improving their learning outcomes and university experience.
```

#### 日本語での補足説明
```
プロジェクト名: TOU Connect - 東京通信大学学生ネットワーキングプラットフォーム

概要:
東京通信大学の学生同士をつなげる教育プラットフォームを開発しています。
通信教育の特性上、学生同士のつながりが希薄になりがちな問題を解決することが目的です。

具体的な用途:
1. プロフィール分析: 公開されているTwitterプロフィールから大学関係者を特定
2. 興味抽出: 公開ツイートから学術的興味や専攻分野を抽出
3. コミュニティ構築: 類似の興味を持つ学習パートナーの発見を支援
4. 学習支援: 課題やプロジェクトでの協力を促進

データ利用方針:
- 公開情報のみを使用
- プライバシーに配慮した匿名化処理
- 学術目的のみの利用
- 商用利用は一切行わない

教育的意義:
通信教育における学生の孤立感を解消し、有意義な学術的関係構築を支援することで、
学習成果と大学体験の向上を目指します。
```

### Step 3: 申請後の流れ

#### 承認までの期間
- 通常: 1-7日
- 学術目的: 比較的早く承認される傾向

#### 承認後の作業
1. Developer Portal にログイン
2. 「Projects & Apps」→「Create App」
3. アプリ名: `TOU Connect`
4. 「Keys and Tokens」タブでBearer Token取得

### Step 4: 環境設定

#### .env ファイル更新
```bash
# 取得したBearer Tokenを設定
TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAA...
```

#### 設定確認
```bash
python check_api_setup.py
```

## 🔧 トラブルシューティング

### よくある申請却下理由と対策

#### 1. 用途が不明確
❌ 「データ分析のため」
✅ 「東京通信大学学生の学習支援コミュニティ構築のため」

#### 2. 商用利用の疑い
❌ 「ビジネス向けプラットフォーム」
✅ 「非営利の教育支援プラットフォーム」

#### 3. プライバシー配慮不足
❌ 「ユーザーデータを収集」
✅ 「公開情報のみ使用、匿名化処理実施」

### 申請が却下された場合
1. 却下理由を確認
2. 用途説明を詳細化
3. プライバシー配慮を強調
4. 再申請（通常24時間後から可能）

## 📊 API制限と最適化

### Basic Plan制限
- 月間10,000ツイート取得
- 15分間に300リクエスト
- ユーザー情報取得: 15分間に75リクエスト

### 効率的な利用方法
1. **キャッシュ実装**: 同じユーザーの重複取得を避ける
2. **バッチ処理**: 複数ユーザーをまとめて処理
3. **優先度設定**: 重要なアカウントを優先的に分析

## 🎯 申請成功のコツ

1. **具体的な教育目的を明記**
2. **プライバシー保護への配慮を強調**
3. **技術的な実装詳細を記載**
4. **非営利・学術目的であることを明確化**
5. **実際の社会的課題解決への貢献を説明**