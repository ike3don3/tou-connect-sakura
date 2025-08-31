#!/usr/bin/env python3
"""
TOU Connect アプリのテストスクリプト
"""
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

def test_environment():
    """環境設定のテスト"""
    print("🔧 環境設定をテスト中...")
    
    # .env ファイルの読み込み
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY が設定されていません")
        return False
    
    print(f"✅ API Key: {api_key[:10]}...")
    
    # Gemini API の設定
    try:
        genai.configure(api_key=api_key)
        print("✅ Gemini API 設定完了")
        return True
    except Exception as e:
        print(f"❌ Gemini API 設定エラー: {e}")
        return False

def test_gemini_api():
    """Gemini API のテスト"""
    print("\n🤖 Gemini API をテスト中...")
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("こんにちは！簡単な挨拶を日本語で返してください。")
        
        if response.text:
            print(f"✅ API レスポンス: {response.text[:50]}...")
            return True
        else:
            print("❌ 空のレスポンス")
            return False
            
    except Exception as e:
        print(f"❌ API エラー: {e}")
        return False

def test_analysis_function():
    """分析機能のテスト"""
    print("\n📊 分析機能をテスト中...")
    
    # ダミーデータで分析テスト
    test_data = {
        "name": "テストユーザー",
        "username": "test_user",
        "bio": "東京通信大学で情報学を学んでいます。プログラミングが好きです。",
        "tweets": "今日はPythonの勉強をしました。機械学習の課題が面白い！ #東京通信大学"
    }
    
    prompt = f"""
    以下のXアカウント情報を分析して、東京通信大学の学生マッチングに必要な情報を抽出してください：

    【プロフィール】
    名前: {test_data['name']}
    ユーザー名: @{test_data['username']}
    自己紹介: {test_data['bio']}
    
    【投稿内容】
    {test_data['tweets']}
    
    以下の項目について簡潔に分析してください：
    1. 大学関係者の可能性（高/中/低）
    2. 興味分野（3つまで）
    3. 学習スタイル
    """
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        if response.text:
            print("✅ 分析結果:")
            print("-" * 40)
            print(response.text)
            print("-" * 40)
            return True
        else:
            print("❌ 分析結果が空です")
            return False
            
    except Exception as e:
        print(f"❌ 分析エラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("🚀 TOU Connect テスト開始\n")
    
    tests = [
        ("環境設定", test_environment),
        ("Gemini API", test_gemini_api),
        ("分析機能", test_analysis_function)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} テストでエラー: {e}")
            results.append((test_name, False))
    
    # 結果サマリー
    print("\n" + "="*50)
    print("📋 テスト結果サマリー")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n合計: {passed}/{len(results)} テスト通過")
    
    if passed == len(results):
        print("🎉 すべてのテストが通過しました！")
        print("次は Webアプリを起動してみましょう:")
        print("  python app.py")
    else:
        print("⚠️  いくつかのテストが失敗しました。設定を確認してください。")

if __name__ == "__main__":
    main()