#!/bin/bash

# TOU Connect プロジェクト情報保存スクリプト
# 作成日: 2025年8月21日
# 目的: プロジェクトの重要情報をバックアップ・保存

echo "=== TOU Connect プロジェクト情報保存 ==="
echo "実行日時: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 基本情報
echo "=== 基本プロジェクト情報 ==="
echo "プロジェクト名: TOU Connect"
echo "ドメイン: touconnect.jp"
echo "VPS IP: 163.43.46.130"
echo "状態: 本番運用中"
echo ""

# アプリケーション情報
echo "=== アプリケーション構成 ==="
echo "Flask アプリ: app_simple.py"
echo "キャッシュ: Redis (cache_manager.py)"
echo "Webサーバー: Nginx"
echo "WSGIサーバー: Gunicorn"
echo "SSL: Let's Encrypt"
echo ""

# 重要ファイルの確認
echo "=== 重要ファイル確認 ==="
important_files=(
    "cache/cache_manager.py"
    "app_simple.py"
    "wsgi.py"
    "gunicorn.conf.py"
    "nginx_touconnect_domain.conf"
    "requirements.txt"
    "setup_domain_nginx.sh"
    "check_dns_status.sh"
)

for file in "${important_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
    fi
done
echo ""

# URL確認
echo "=== アクセス可能URL ==="
urls=(
    "https://touconnect.jp"
    "https://www.touconnect.jp"
    "https://touconnect.jp/health"
)

for url in "${urls[@]}"; do
    echo "📱 $url"
done
echo ""

# 運用コマンド
echo "=== 重要な運用コマンド ==="
echo "DNS確認: dig +short touconnect.jp"
echo "SSL確認: sudo certbot certificates"
echo "Nginx テスト: sudo nginx -t"
echo "アプリ再起動: sudo systemctl restart gunicorn"
echo "Redis 再起動: sudo systemctl restart redis-server"
echo ""

# バックアップ情報
echo "=== バックアップ・ドキュメント ==="
echo "📁 プロジェクトアーカイブ: PROJECT_FINAL_ARCHIVE_20250821.md"
echo "📁 完了レポート: PROJECT_COMPLETION_REPORT.md"
echo "📁 展開準備: DEPLOYMENT_READY.md"
echo "📁 運用サポート: LIVE_APPLICATION_SUPPORT.md"
echo ""

# 統計情報
echo "=== プロジェクト統計 ==="
echo "総ファイル数: $(find . -type f | wc -l)"
echo "総ディレクトリ数: $(find . -type d | wc -l)"
echo "Pythonファイル数: $(find . -name "*.py" | wc -l)"
echo "マークダウンファイル数: $(find . -name "*.md" | wc -l)"
echo "設定ファイル数: $(find . -name "*.conf" -o -name "*.yml" -o -name "*.yaml" | wc -l)"
echo ""

echo "=== 保存完了 ==="
echo "プロジェクト情報の保存が完了しました。"
echo "全ての重要な情報とドキュメントが整理されています。"
echo ""
echo "次回アクセス時は以下を参照してください："
echo "- PROJECT_FINAL_ARCHIVE_20250821.md (包括的なプロジェクト情報)"
echo "- このスクリプト ($0) で現在の状態確認"
echo ""
echo "プロジェクト完了おめでとうございます！ 🎉"
