# 5分で完了！Twitter API申請クイックガイド

## 🚀 超簡単申請手順

### Step 1: ログイン（1分）
1. https://developer.twitter.com/en/portal/dashboard を開く
2. 「Sign up for Free Account」をクリック
3. @ike3don3 でログイン

### Step 2: 基本情報（1分）
- **Name**: あなたの実名
- **Country**: Japan
- **Use case**: Academic research

### Step 3: プロジェクト説明（3分）
以下をコピー&ペーストするだけ：

#### Project Name:
```
TOU Connect - Student Networking Platform
```

#### How will you use Twitter data?
```
I am developing an educational platform to help Tokyo Online University students connect with each other. The platform analyzes public Twitter profiles to identify university-related accounts and extract academic interests, helping students find study partners with similar goals.

Key features:
- Analyze public profiles to identify TOU students
- Extract academic interests from public tweets
- Help students find study partners
- Facilitate academic collaboration

Privacy & Ethics:
- Only public information accessed
- No private messages or protected content
- Educational purpose only
- Data anonymized and aggregated
- No commercial use or data resale
```

#### Will you make Twitter content available to a government entity?
```
No
```

#### Will you display Twitter content off Twitter?
```
Only aggregated, anonymized insights for educational matching. No individual tweets displayed.
```

### Step 4: 送信（30秒）
- 内容を確認
- 「Submit」をクリック
- 完了！

## ⏰ 申請後の流れ

### 承認通知（1-7日後）
- メールで通知が届きます
- 通常3-5日で承認されます

### 承認後の設定（2分）
1. Developer Portal にログイン
2. 「Create App」→ アプリ名「TOU Connect」
3. 「Keys and Tokens」タブ
4. Bearer Token をコピー
5. .env ファイルに貼り付け：
   ```
   TWITTER_BEARER_TOKEN=your_token_here
   ```

## 🎉 完了後
```bash
python api_status_tracker.py
```
で動作確認！

## 📞 困った時のサポート
- 申請で不明な点があれば質問してください
- 承認後の設定もサポートします
- 開発は現在のモックデータで継続可能です