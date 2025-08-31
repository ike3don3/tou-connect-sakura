#!/usr/bin/env python3
"""
TOU Connect - 本番用起動スクリプト
Gunicornを使用した本番環境での実行
"""

import os
import sys
import logging
from app_simple import create_simple_app

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# アプリケーション作成
app = create_simple_app()

if __name__ == '__main__':
    # 開発サーバーとして実行する場合
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=False)
