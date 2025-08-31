# 🔧 さくらVPS SSH接続設定ガイド

## 📋 接続情報
- **IPアドレス**: 153.127.55.224
- **初期ユーザー**: root
- **SSH設定**: 初回セットアップが必要

## 🔑 SSH接続設定手順

### ステップ1: さくらVPS管理画面での確認
1. さくらのVPS管理画面にログイン
2. 「サーバー情報」でSSH接続情報を確認
3. 初期パスワードまたはSSH鍵設定を確認

### ステップ2: SSH鍵生成（ローカル）
```bash
# SSH鍵ペア生成（まだない場合）
ssh-keygen -t rsa -b 4096 -C "touconnect@vps"

# 公開鍵表示
cat ~/.ssh/id_rsa.pub
```

### ステップ3: VPSでの鍵設定
さくらVPS管理画面または初回SSH接続で：

```bash
# VPSにログイン後（パスワード認証）
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 公開鍵を追加（ローカルの ~/.ssh/id_rsa.pub の内容をコピー）
echo "ssh-rsa AAAAB3NzaC1yc2E... [公開鍵の内容]" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### ステップ4: SSH設定確認
```bash
# ローカルから接続テスト
ssh -o ConnectTimeout=10 root@153.127.55.224 "echo 'SSH接続成功'"
```

## 🚀 自動初期設定実行

SSH接続が確立できたら、以下のコマンドで自動初期設定を実行：

```bash
# 1. 初期設定スクリプトをVPSにアップロード
scp vps_initial_setup.sh root@153.127.55.224:/tmp/

# 2. VPSで実行
ssh root@153.127.55.224 "bash /tmp/vps_initial_setup.sh"
```

## 📞 トラブルシューティング

### 接続できない場合
1. **ファイアウォール**: さくらVPS管理画面でSSH (22番ポート) が開放されているか確認
2. **パスワード認証**: 一時的にパスワード認証を有効にして接続
3. **VPSの状態**: 管理画面でVPSが稼働中か確認

### パスワード認証での初回接続
```bash
# パスワード認証で接続（初回のみ）
ssh -o PreferredAuthentications=password root@153.127.55.224
```

---

## 🔄 次のステップ

1. ✅ SSH接続設定完了
2. 🔄 VPS初期設定実行
3. 🔄 アプリケーションデプロイ
4. 🔄 DNS設定確認
5. 🔄 SSL証明書取得

**現在のフェーズ**: SSH接続設定  
**次のフェーズ**: VPS初期設定
