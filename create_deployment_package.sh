#!/bin/bash
# デプロイパッケージ作成スクリプト

echo "🚀 TOU Connect デプロイパッケージ作成中..."

# デプロイパッケージディレクトリ作成
mkdir -p deployment_package

# 必要なファイルをコピー
cp -r . deployment_package/tou_connect/

# 不要なファイルを除外
cd deployment_package/tou_connect/
rm -rf .git __pycache__ *.pyc .pytest_cache venv node_modules

# 圧縮
cd ..
tar -czf tou_connect_deployment.tar.gz tou_connect/

echo "✅ デプロイパッケージ作成完了: deployment_package/tou_connect_deployment.tar.gz"
echo ""
echo "📋 次のステップ:"
echo "1. deployment_package/tou_connect_deployment.tar.gz をダウンロード"
echo "2. さくらのVPSのファイルマネージャーまたはFTPでアップロード"
echo "3. サーバーで展開: tar -xzf tou_connect_deployment.tar.gz"
echo "4. デプロイスクリプト実行: cd tou_connect && sudo ./deploy_sakura.sh"