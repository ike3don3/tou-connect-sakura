#!/usr/bin/env python3
"""
本番環境準備状況チェック
一般公開に向けた準備度を評価
"""
import os
import sys
from pathlib import Path

def check_security():
    """セキュリティ関連のチェック"""
    print("🔒 セキュリティチェック")
    issues = []
    
    # .envファイルのチェック
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
            
        # APIキーが露出していないかチェック
        if 'AIzaSy' in env_content:
            issues.append("❌ Gemini APIキーが.envファイルに平文で保存されています")
        
        if 'AAAAAAAA' in env_content:
            issues.append("❌ Twitter Bearer Tokenが.envファイルに平文で保存されています")
    
    # SECRET_KEYのチェック
    if 'dev-secret-key' in env_content:
        issues.append("❌ 開発用SECRET_KEYが使用されています")
    
    # データベースファイルのチェック
    if Path('tou_connect.db').exists():
        issues.append("⚠️ SQLiteファイルが本番環境で使用されています（スケーラビリティの問題）")
    
    if not issues:
        print("  ✅ 基本的なセキュリティ問題は見つかりませんでした")
    else:
        for issue in issues:
            print(f"  {issue}")
    
    return len(issues) == 0

def check_production_config():
    """本番環境設定のチェック"""
    print("\n⚙️ 本番環境設定チェック")
    issues = []
    
    # デバッグモードのチェック
    with open('app.py', 'r') as f:
        app_content = f.read()
        
    if 'debug=True' in app_content:
        issues.append("❌ Flaskのデバッグモードが有効になっています")
    
    if 'app.run(' in app_content:
        issues.append("❌ 開発サーバーが使用されています（本番ではWSGIサーバーが必要）")
    
    # ログ設定のチェック
    if 'logging' not in app_content:
        issues.append("⚠️ 本格的なログ設定がありません")
    
    if not issues:
        print("  ✅ 基本的な設定問題は見つかりませんでした")
    else:
        for issue in issues:
            print(f"  {issue}")
    
    return len(issues) == 0

def check_privacy_compliance():
    """プライバシー・法的コンプライアンスのチェック"""
    print("\n🛡️ プライバシー・法的コンプライアンスチェック")
    issues = []
    
    # プライバシーポリシーの存在チェック
    if not Path('templates/privacy.html').exists():
        issues.append("❌ プライバシーポリシーページがありません")
    
    if not Path('templates/terms.html').exists():
        issues.append("❌ 利用規約ページがありません")
    
    # データ削除機能のチェック
    with open('repositories/user_repository.py', 'r') as f:
        user_repo_content = f.read()
        
    if 'delete_user' not in user_repo_content:
        issues.append("⚠️ ユーザーデータ削除機能が不完全です")
    
    # 同意取得機能のチェック
    with open('templates/index.html', 'r') as f:
        index_content = f.read()
        
    if 'プライバシーポリシー' not in index_content:
        issues.append("❌ プライバシーポリシーへの同意取得がありません")
    
    if not issues:
        print("  ✅ 基本的なプライバシー要件は満たされています")
    else:
        for issue in issues:
            print(f"  {issue}")
    
    return len(issues) == 0

def check_scalability():
    """スケーラビリティのチェック"""
    print("\n📈 スケーラビリティチェック")
    issues = []
    
    # データベース設計
    if Path('tou_connect.db').exists():
        issues.append("⚠️ SQLiteは大規模運用に適していません（PostgreSQL推奨）")
    
    # キャッシュ機能
    with open('app.py', 'r') as f:
        app_content = f.read()
        
    if 'cache' not in app_content.lower():
        issues.append("⚠️ キャッシュ機能がありません")
    
    # レート制限
    if 'rate_limit' not in app_content.lower():
        issues.append("⚠️ API レート制限がありません")
    
    # 非同期処理
    if 'celery' not in app_content.lower() and 'async' not in app_content.lower():
        issues.append("⚠️ 重い処理の非同期化がありません")
    
    if not issues:
        print("  ✅ スケーラビリティの基本要件は満たされています")
    else:
        for issue in issues:
            print(f"  {issue}")
    
    return len(issues) == 0

def check_monitoring():
    """監視・運用のチェック"""
    print("\n📊 監視・運用チェック")
    issues = []
    
    # ヘルスチェックエンドポイント
    with open('app.py', 'r') as f:
        app_content = f.read()
        
    if '/health' not in app_content:
        issues.append("❌ ヘルスチェックエンドポイントがありません")
    
    # エラーハンドリング
    if '@app.errorhandler' not in app_content:
        issues.append("❌ グローバルエラーハンドラーがありません")
    
    # メトリクス収集
    if 'prometheus' not in app_content.lower() and 'metrics' not in app_content.lower():
        issues.append("⚠️ メトリクス収集機能がありません")
    
    if not issues:
        print("  ✅ 基本的な監視要件は満たされています")
    else:
        for issue in issues:
            print(f"  {issue}")
    
    return len(issues) == 0

def generate_production_recommendations():
    """本番環境への推奨事項"""
    print("\n🚀 本番環境への推奨事項")
    
    recommendations = [
        "1. 環境変数管理",
        "   - AWS Secrets Manager / Azure Key Vault の使用",
        "   - 環境別設定ファイルの分離",
        "",
        "2. データベース",
        "   - PostgreSQL / MySQL への移行",
        "   - 接続プール設定",
        "   - バックアップ戦略",
        "",
        "3. インフラ",
        "   - Docker コンテナ化",
        "   - Kubernetes / AWS ECS でのデプロイ",
        "   - CDN の設定（静的ファイル配信）",
        "",
        "4. セキュリティ",
        "   - HTTPS 強制",
        "   - CORS 設定",
        "   - CSP (Content Security Policy)",
        "   - レート制限",
        "",
        "5. 監視・ログ",
        "   - APM ツール (New Relic, DataDog)",
        "   - 構造化ログ",
        "   - アラート設定",
        "",
        "6. 法的対応",
        "   - プライバシーポリシー作成",
        "   - 利用規約作成",
        "   - GDPR / 個人情報保護法対応",
        "",
        "7. パフォーマンス",
        "   - Redis キャッシュ",
        "   - CDN 設定",
        "   - 画像最適化",
        "",
        "8. CI/CD",
        "   - GitHub Actions / GitLab CI",
        "   - 自動テスト",
        "   - 段階的デプロイ"
    ]
    
    for rec in recommendations:
        print(f"  {rec}")

def main():
    """メインチェック実行"""
    print("🔍 TOU Connect 本番環境準備状況チェック")
    print("=" * 60)
    
    checks = [
        ("セキュリティ", check_security),
        ("本番環境設定", check_production_config),
        ("プライバシー・法的コンプライアンス", check_privacy_compliance),
        ("スケーラビリティ", check_scalability),
        ("監視・運用", check_monitoring)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ チェック中にエラー: {e}")
            results.append((name, False))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📋 チェック結果サマリー")
    print("=" * 60)
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ NEEDS WORK"
        print(f"{name:30s}: {status}")
        if result:
            passed += 1
    
    print(f"\n合計: {passed}/{len(results)} 項目が本番環境準備完了")
    
    # 総合判定
    if passed == len(results):
        print("\n🎉 本番環境準備完了！一般公開可能です")
        readiness = "READY"
    elif passed >= len(results) * 0.7:
        print("\n⚠️ 基本機能は準備完了。いくつかの改善が推奨されます")
        readiness = "MOSTLY_READY"
    else:
        print("\n❌ 本番環境準備が不十分です。重要な問題を解決してください")
        readiness = "NOT_READY"
    
    generate_production_recommendations()
    
    return readiness

if __name__ == "__main__":
    readiness = main()
    print(f"\n🎯 総合判定: {readiness}")