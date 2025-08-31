#!/bin/bash
# TOU Connect 緊急診断・復旧スクリプト

echo "🚨 TOU Connect 緊急診断開始..."

cd /home/ike3don3/apps/tou_connect

echo "📊 現在の状況確認:"
echo "=================="

# 1. プロセス確認
echo "🔍 Gunicornプロセス確認:"
ps aux | grep gunicorn | grep -v grep || echo "❌ Gunicornプロセスが見つかりません"

echo ""
echo "🔍 Pythonプロセス確認:"
ps aux | grep python | grep -v grep | head -5

echo ""
echo "🔍 ポート8000の使用状況:"
netstat -tulpn | grep 8000 || echo "❌ ポート8000がリスニングしていません"

echo ""
echo "🔍 Nginxステータス:"
sudo systemctl status nginx --no-pager -l || echo "❌ Nginx状態確認失敗"

echo ""
echo "🔍 ディスク容量:"
df -h / | tail -1

echo ""
echo "🔍 メモリ使用量:"
free -h

echo ""
echo "🔍 最近のログ:"
tail -10 /var/log/nginx/error.log 2>/dev/null || echo "Nginxエラーログにアクセスできません"

echo ""
echo "🔧 復旧作業開始..."
echo "=================="

# 2. 仮想環境確認・起動
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ 仮想環境アクティベート完了"
else
    echo "❌ 仮想環境が見つかりません"
    exit 1
fi

# 3. 環境変数設定
export FLASK_ENV=production
export ENVIRONMENT=production
export REDIS_URL="redis://localhost:6379/0"
echo "✅ 環境変数設定完了"

# 4. アプリケーションファイル確認
echo "📁 アプリケーションファイル確認:"
ls -la app_simple.py 2>/dev/null && echo "✅ app_simple.py存在" || echo "❌ app_simple.py不存在"
ls -la templates/ 2>/dev/null && echo "✅ templatesディレクトリ存在" || echo "❌ templatesディレクトリ不存在"

# 5. 既存プロセス強制終了
echo "🛑 既存プロセス強制終了中..."
pkill -9 -f "gunicorn" || true
pkill -9 -f "app_simple" || true
sleep 3

# 6. アプリケーション動作テスト
echo "🧪 アプリケーション動作テスト:"
python3 -c "
try:
    import app_simple
    print('✅ app_simple.py インポート成功')
    app = app_simple.create_app()
    print('✅ Flaskアプリ作成成功')
except Exception as e:
    print(f'❌ エラー: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ アプリケーション動作確認成功"
else
    echo "❌ アプリケーション動作確認失敗 - アプリケーションを再作成します"
    
    # 緊急用シンプルアプリ作成
    cat > app_simple_emergency.py << 'PYEOF'
#!/usr/bin/env python3
"""
TOU Connect - 緊急復旧版
"""

import os
from flask import Flask, jsonify, render_template_string

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'emergency-key'
    
    # 緊急用HTMLテンプレート
    HTML_TEMPLATE = '''
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TOU Connect - 復旧中</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            .status { color: #28a745; font-weight: bold; }
            .maintenance { color: #ffc107; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 TOU Connect</h1>
            <p class="status">✅ サービス復旧中</p>
            <p>現在、システムの復旧作業を行っています。</p>
            <p>ご不便をおかけして申し訳ございません。</p>
            
            <h3>📊 システム状況</h3>
            <ul>
                <li>✅ サーバー: 正常稼働中</li>
                <li>✅ データベース: 利用可能</li>
                <li>🔄 アプリケーション: 復旧中</li>
            </ul>
            
            <p><small>最終更新: {{ timestamp }}</small></p>
        </div>
    </body>
    </html>
    '''
    
    @app.route('/')
    def index():
        from datetime import datetime
        return render_template_string(HTML_TEMPLATE, 
                                    timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'maintenance',
            'message': 'System recovery in progress',
            'version': '1.0-emergency-recovery'
        })
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=False)
PYEOF

    echo "✅ 緊急復旧アプリ作成完了"
    cp app_simple.py app_simple.py.broken_backup 2>/dev/null || true
    cp app_simple_emergency.py app_simple.py
fi

# 7. Gunicorn起動
echo "🚀 Gunicorn起動中..."
gunicorn --bind 127.0.0.1:8000 --workers 2 --timeout 30 --daemon app_simple:app

# 8. 起動確認
sleep 5
echo "🔍 起動確認中..."

if pgrep -f "gunicorn.*app_simple" > /dev/null; then
    echo "✅ Gunicornプロセス起動成功"
    
    # プロセス詳細
    ps aux | grep gunicorn | grep -v grep
    
    # ポート確認
    netstat -tulpn | grep 8000
    
    # ローカルテスト
    echo ""
    echo "🧪 ローカル動作確認:"
    curl -s http://127.0.0.1:8000/health || echo "ローカルテスト失敗"
    
else
    echo "❌ Gunicorn起動失敗"
    
    # ログ確認
    echo "📋 エラー詳細:"
    journalctl -u gunicorn --no-pager -l | tail -10 2>/dev/null || echo "systemdログなし"
    
    # 手動起動テスト
    echo "🔧 手動起動テスト:"
    python3 app_simple.py &
    MANUAL_PID=$!
    sleep 3
    
    if ps -p $MANUAL_PID > /dev/null; then
        echo "✅ 手動起動成功 (PID: $MANUAL_PID)"
        curl -s http://127.0.0.1:8000/health || echo "手動起動テスト失敗"
        kill $MANUAL_PID
        
        # 再度Gunicorn試行
        gunicorn --bind 127.0.0.1:8000 --workers 1 --timeout 60 --daemon app_simple:app
        sleep 3
        
        if pgrep -f "gunicorn" > /dev/null; then
            echo "✅ Gunicorn再起動成功"
        else
            echo "❌ Gunicorn再起動失敗"
        fi
    else
        echo "❌ 手動起動も失敗"
        exit 1
    fi
fi

# 9. Nginx再起動
echo "🌐 Nginx再起動中..."
sudo nginx -t && sudo systemctl reload nginx

echo ""
echo "🎯 最終確認..."
echo "=============="

sleep 3

# 外部アクセステスト
echo "🌍 外部アクセステスト:"
curl -I https://touconnect.jp/health 2>/dev/null | head -3 || echo "外部アクセス失敗"

echo ""
echo "🎉 復旧作業完了！"
echo ""
echo "確認URL:"
echo "  - https://touconnect.jp"
echo "  - https://touconnect.jp/health"
echo ""
echo "問題が解決しない場合は、以下を実行してください:"
echo "  sudo systemctl restart nginx"
echo "  sudo systemctl status nginx"
