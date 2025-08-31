# 🌐 DNS設定手順 - お名前.com

## 📋 設定情報
- **ドメイン**: touconnect.jp
- **VPS IPアドレス**: 153.127.55.224
- **DNS サービス**: お名前.com

## 🔧 DNS設定手順

### ステップ1: お名前.com管理画面にログイン
1. https://www.onamae.com/ にアクセス
2. 「お名前ID」と「パスワード」でログイン

### ステップ2: DNS設定画面に移動
1. 管理画面で「DNS設定/転送設定」をクリック
2. 「DNSレコード設定」を選択
3. 対象ドメイン「touconnect.jp」を選択

### ステップ3: Aレコード設定
以下の2つのAレコードを追加してください：

```
ホスト名: @
TYPE: A
VALUE: 153.127.55.224
TTL: 300 (または デフォルト)
```

```
ホスト名: www
TYPE: A  
VALUE: 153.127.55.224
TTL: 300 (または デフォルト)
```

### ステップ4: 設定保存
- 「追加」ボタンをクリック
- 設定内容を確認
- 「確認画面へ進む」→「設定する」

## ⏰ DNS反映時間
- **通常**: 30分〜2時間
- **最大**: 48時間
- **確認方法**: `dig touconnect.jp` コマンド

## ✅ 設定確認方法

### ローカルから確認
```bash
# touconnect.jp の確認
dig touconnect.jp A
nslookup touconnect.jp

# www.touconnect.jp の確認  
dig www.touconnect.jp A
nslookup www.touconnect.jp
```

### 期待される結果
```
touconnect.jp.    300    IN    A    153.127.55.224
www.touconnect.jp. 300   IN    A    153.127.55.224
```

## 🚨 よくある問題

### 1. DNS反映されない
- 設定から最大48時間待機
- TTL設定を確認
- キャッシュクリア: `sudo dscacheutil -flushcache`

### 2. 設定画面が見つからない
- お名前.com の新UIの場合は「DNS」→「DNSレコード設定」
- 旧UIの場合は「DNS設定/転送設定」→「DNSレコード設定」

---

## 📞 次のステップ

DNS設定完了後、以下のコマンドでVPSデプロイを開始してください：

```bash
./deploy_to_vps.sh 153.127.55.224
```

**作成日**: 2025年8月18日  
**IPアドレス**: 153.127.55.224  
**ステータス**: DNS設定待ち
