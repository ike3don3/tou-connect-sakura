# 🚨 TOU Connect 緊急修正 - 即座実行版

## 現在の問題
- ✅ DNS設定: 正常
- ✅ SSL証明書: 有効
- ❌ アプリケーション: 502エラー（Flaskアプリ停止中）

## 🔧 即座修正手順（VPSで実行）

### 1. SSH接続
```bash
ssh ike3don3@153.127.55.224
```

### 2. ワンライナー修正コマンド
```bash
cd /home/ike3don3/apps/tou_connect && source venv/bin/activate && sudo pkill -f gunicorn && export FLASK_ENV=production && gunicorn --bind 127.0.0.1:8000 --workers 2 --daemon app_simple:app && sudo systemctl reload nginx && curl -I http://127.0.0.1:8000/health
```

### 3. 確認
```bash
# プロセス確認
ps aux | grep gunicorn

# 外部接続確認  
curl -I https://touconnect.jp/health
```

## 🎯 期待される結果
- HTTPSアクセス: ✅ 200 OK
- ヘルスチェック: ✅ 正常レスポンス
- メインサイト: ✅ 完全動作

---

**修正時間目安**: 2-3分  
**修正成功後**: https://touconnect.jp で完全アクセス可能
