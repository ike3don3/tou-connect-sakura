# 🌐 DNS設定ガイド（お名前.com）

## 📋 DNS設定手順

### お名前.com DNS設定
1. **お名前.com Naviにログイン**
   - https://www.onamae.com/

2. **DNS設定メニューへ**
   - 「ドメイン」→「DNS設定」

3. **Aレコード設定**
   ```
   ホスト名: @ (または空白)
   TYPE: A
   VALUE: [さくらVPSのIPアドレス]
   TTL: 3600
   ```

4. **WWWサブドメイン設定**
   ```
   ホスト名: www
   TYPE: A  
   VALUE: [さくらVPSのIPアドレス]
   TTL: 3600
   ```

### 設定例
```
# さくらVPSのIPが 203.0.113.10 の場合
@ A 203.0.113.10
www A 203.0.113.10
```

### 反映時間
- **通常**: 1-24時間
- **確認方法**: `nslookup touconnect.jp`

## 📝 設定完了チェック

DNS設定が完了したら、以下で確認：

```bash
# ローカルで確認
nslookup touconnect.jp
nslookup www.touconnect.jp

# 期待される結果
# Address: [さくらVPSのIPアドレス]
```

---
**さくらVPSのIPアドレスを教えてください** 👆
