#!/bin/bash

# ポート8000を開放するスクリプト
echo "ポート8000を開放します..."

# UFWでポート8000を許可
echo "sudo ufw allow 8000" | sudo -S sh

# iptablesでもポート8000を許可（念のため）
echo "sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT" | sudo -S sh

# ファイアウォールのステータスを確認
echo "現在のファイアウォール設定:"
sudo ufw status verbose

echo "ポート開放スクリプト完了"
