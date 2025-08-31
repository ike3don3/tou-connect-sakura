# 🌍 TOU Connect 一般公開ガイド

## 🚀 最も簡単な公開方法: Railway

### Step 1: Railwayアカウント作成 (5分)
1. https://railway.app にアクセス
2. GitHubアカウントでサインアップ
3. 無料プラン選択 (月500時間まで)

### Step 2: プロジェクトデプロイ (10分)
```bash
# Railway CLI インストール
npm install -g @railway/cli

# ログイン
railway login

# プロジェクト作成
railway init
railway add

# デプロイ
railway up
```

### Step 3: 環境変数設定 (5分)
Railway ダッシュボードで設定:
- `GEMINI_API_KEY`
- `TWITTER_BEARER_TOKEN`
- `SECRET_KEY`

### Step 4: 自動URL取得
Railway が自動で URL を生成:
`https://your-app-name.railway.app`

## 🌟 さらに簡単: ngrok (テスト用)

### 今すぐ一時公開 (2分)
```bash
# ngrok インストール
brew install ngrok

# 現在のサーバーを一時公開
ngrok http 8000
```

これで一時的な公開URL取得:
`https://abc123.ngrok.io`

## ⚡ 超高速デプロイ: Vercel (フロントエンド特化)

### Step 1: Vercel準備
```bash
npm install -g vercel
vercel login
```

### Step 2: デプロイ
```bash
vercel --prod
```

自動URL: `https://tou-connect.vercel.app`

---

## 💡 推奨アプローチ

**段階的公開:**
1. **今日**: ngrok で一時公開 (友人テスト)
2. **今週**: Railway で本格公開
3. **来月**: 独自ドメイン + SSL

**費用:**
- ngrok: 無料 (制限あり)
- Railway: 無料 → 月$5
- 独自ドメイン: 年間$10-15
