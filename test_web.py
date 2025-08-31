#!/usr/bin/env python3
"""
Web アプリケーションのテスト
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import app
import json

def test_flask_app():
    """Flask アプリのテスト"""
    print("🌐 Flask アプリをテスト中...")
    
    # テストクライアントを作成
    app.config['TESTING'] = True
    client = app.test_client()
    
    try:
        # メインページのテスト
        print("  📄 メインページをテスト...")
        response = client.get('/')
        if response.status_code == 200:
            print("  ✅ メインページ: OK")
        else:
            print(f"  ❌ メインページ: {response.status_code}")
            return False
        
        # 分析APIのテスト
        print("  🔍 分析APIをテスト...")
        test_data = {"username": "test_user"}
        response = client.post('/analyze', 
                             data=json.dumps(test_data),
                             content_type='application/json')
        
        if response.status_code == 200:
            result = response.get_json()
            if result and 'analysis' in result:
                print("  ✅ 分析API: OK")
                print(f"  📊 分析結果の一部: {result['analysis'][:100]}...")
                return True
            else:
                print("  ❌ 分析API: レスポンス形式エラー")
                return False
        else:
            print(f"  ❌ 分析API: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ テストエラー: {e}")
        return False

def main():
    """メインテスト"""
    print("🚀 Web アプリケーション テスト開始\n")
    
    if test_flask_app():
        print("\n🎉 Webアプリのテストが成功しました！")
        print("\n次のステップ:")
        print("1. アプリを起動: python app.py")
        print("2. ブラウザで http://localhost:5001 にアクセス")
        print("3. テストユーザー名を入力して分析を試してみてください")
    else:
        print("\n❌ Webアプリのテストが失敗しました")

if __name__ == "__main__":
    main()