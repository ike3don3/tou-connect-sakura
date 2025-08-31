#!/usr/bin/env python3
"""
サーバー起動スクリプト
"""
import os
import webbrowser
import time
from threading import Timer
from app import app

def open_browser():
    """ブラウザを自動で開く"""
    webbrowser.open('http://localhost:5001')

if __name__ == '__main__':
    print("🚀 TOU Connect サーバーを起動中...")
    print("📱 ブラウザが自動で開きます...")
    print("🔗 URL: http://localhost:5002")
    print("⏹️  停止するには Ctrl+C を押してください")
    print("-" * 50)
    
    # 1秒後にブラウザを開く
    def open_browser_delayed():
        webbrowser.open('http://localhost:5002')
    Timer(1.0, open_browser_delayed).start()
    
    # Flaskアプリを起動
    app.run(debug=True, port=5002, use_reloader=False)