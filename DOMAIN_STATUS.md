## 🌐 ドメイン設定確認・完了ガイド

### 📋 現在の状況 (2025年8月19日 21:30)
- **ドメイン**: touconnect.jp (取得済み)
- **VPS**: 153.127.55.224 (動作中)
- **アプリケーション**: ✅ 正常動作 (http://153.127.55.224/)
- **DNS設定**: ❌ 未反映

### 🔧 DNS設定が必要なレコード

**お名前.com管理画面で設定してください：**

```
ホスト名: @
TYPE: A
VALUE: 153.127.55.224
TTL: 300
```

```
ホスト名: www
TYPE: A
VALUE: 153.127.55.224
TTL: 300
```

### ✅ DNS設定完了後のアクセス先
- メインサイト: http://touconnect.jp/
- WWWサイト: http://www.touconnect.jp/
- ヘルスチェック: http://touconnect.jp/health

### 🔒 SSL証明書設定コマンド (DNS完了後)
```bash
ssh ike3don3@153.127.55.224 "sudo ./setup_dns_ssl.sh"
```

### 📊 DNS反映確認コマンド
```bash
dig +short touconnect.jp
nslookup touconnect.jp
curl -I http://touconnect.jp/health
```

---
**ステータス**: DNS設定待ち → 完了後にSSL設定予定
**最終更新**: 2025年8月19日
