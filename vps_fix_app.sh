#!/bin/bash
# VPS上でapp_simple.pyの「非公開」表示問題を修正するスクリプト

cd /home/ike3don3/apps/tou_connect

# バックアップ作成
cp app_simple.py app_simple.py.backup

# 主要な修正を適用
cat > temp_fix.py << 'EOF'
# app_simple.pyの「非公開」表示問題修正

import re

# ファイル読み込み
with open('app_simple.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 「非公開」→「取得中」に変更
content = re.sub(r'"非公開"', '"取得中"', content)
content = re.sub(r"'非公開'", "'取得中'", content)

# 2. プロフィール取得エラー時のメッセージ改善
content = re.sub(
    r'return \{"error": "プロフィール情報の取得に失敗しました"\}',
    'return {"error": "プロフィール情報を取得中です。しばらくお待ちください。"}',
    content
)

# 3. API制限エラーのメッセージ改善
content = re.sub(
    r'"API制限に達しました"',
    '"現在多くのリクエストを処理中です。少し時間をおいてから再度お試しください。"',
    content
)

# ファイル保存
with open('app_simple.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ app_simple.py の修正が完了しました")
EOF

python3 temp_fix.py
rm temp_fix.py

echo "✅ 修正完了 - app_simple.pyが更新されました"
