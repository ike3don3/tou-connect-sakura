# Twitter API v2 設定ガイド

## 1. X Developer Portal アカウント作成

### ステップ 1: 申請
1. https://developer.twitter.com/en/portal/dashboard にアクセス
2. 「Sign up for Free Account」をクリック
3. 既存のXアカウントでログイン

### ステップ 2: 用途の説明
申請時に以下のような内容を記載してください：

**使用目的（英語で記載）:**
```
I am developing an educational platform for Tokyo Online University students to help them connect with each other. The application will analyze public Twitter profiles and tweets to:

1. Identify university-related accounts
2. Extract interests and academic fields
3. Facilitate student networking and collaboration
4. Support online learning community building

This is for academic research and educational purposes only, focusing on public information to help distance learning students find study partners and build academic connections.
```

**日本語訳:**
```
東京通信大学の学生同士をつなげる教育プラットフォームを開発しています。
公開されているTwitterプロフィールとツイートを分析して：

1. 大学関係のアカウントを特定
2. 興味や学術分野を抽出
3. 学生のネットワーキングと協力を促進
4. オンライン学習コミュニティの構築を支援

これは学術研究と教育目的のみで、公開情報を使用して通信教育の学生が
学習パートナーを見つけ、学術的なつながりを構築することを支援します。
```

## 2. API キーの取得

### 承認後の手順:
1. Developer Portal にログイン
2. 「Projects & Apps」→「Create App」
3. アプリ名: `TOU Connect`
4. 「Keys and Tokens」タブ
5. **Bearer Token** をコピー

## 3. 環境変数の設定

`.env` ファイルに以下を追加：
```
TWITTER_BEARER_TOKEN=your_actual_bearer_token_here
```

## 4. API 制限について

### Basic Plan (無料):
- 月間 10,000 ツイート取得
- レート制限: 15分間に300リクエスト
- 学術研究目的なら十分

### 使用量の最適化:
- キャッシュ機能の実装
- バッチ処理での効率化
- 必要最小限のデータ取得

## 5. トラブルシューティング

### よくある問題:
1. **401 Unauthorized**: Bearer Tokenが間違っている
2. **403 Forbidden**: API制限に達している
3. **404 Not Found**: ユーザーが存在しない/非公開

### 解決方法:
- `.env` ファイルの確認
- API使用量の確認
- アカウント名の確認（@マーク除去）