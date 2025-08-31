# 🚀 デプロイメント設定バックアップ

## VPS接続情報
- **IP**: 153.127.55.224
- **ユーザー**: ike3don3
- **SSH**: 公開鍵認証設定済み

## アプリケーション設定

### メインアプリ (app_simple.py)
```python
# 現在動作中のFlaskアプリケーション
# ポート: 8000
# 機能: ヘルスチェック、メインページ、キャッシュ対応
```

### Nginx設定 (nginx_touconnect.conf)
```nginx
server {
    listen 80;
    server_name 153.127.55.224;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### DNS設定記録
```
Domain: touconnect.jp
Provider: お名前.com

Aレコード設定:
@ (root) -> 153.127.55.224
www -> 153.127.55.224

設定完了: 2025年8月19日 21:15
反映予定: 2025年8月19日 21:45〜23:15
```

### Redis キャッシュ設定
```python
# cache_manager.py の設定
REDIS_URL = "redis://localhost:6379/0"
キャッシュ戦略:
- user_data: 30分
- analysis_results: 2時間
- matching_results: 1時間
- api_responses: 5分
- session_data: 24時間
- static_content: 24時間
```

## 起動コマンド
```bash
# VPS上でのアプリケーション起動
cd touconnect && source venv/bin/activate && nohup python app.py > app.log 2>&1 &
```

## 確認コマンド
```bash
# DNS確認
dig +short touconnect.jp A

# アプリケーション確認
curl -s http://153.127.55.224/health

# プロセス確認
ssh ike3don3@153.127.55.224 "ps aux | grep python"
```
