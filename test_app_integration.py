#!/usr/bin/env python3
"""
統合されたFlaskアプリのテスト
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import app
import json

def test_integrated_app():
    """統合されたアプリのテスト"""
    print("🌐 統合Flaskアプリテスト開始")
    
    # テストクライアントを作成
    app.config['TESTING'] = True
    client = app.test_client()
    
    try:
        # 1. メインページのテスト
        print("✅ メインページテスト")
        response = client.get('/')
        if response.status_code == 200:
            print("  メインページ: OK")
            # マッチングリンクが含まれているかチェック
            if '学友マッチング'.encode('utf-8') in response.data:
                print("  マッチングリンク: OK")
        
        # 2. マッチングページのテスト
        print("✅ マッチングページテスト")
        response = client.get('/matching')
        if response.status_code == 200:
            print("  マッチングページ: OK")
        
        # 3. プロフィールAPI のテスト
        print("✅ プロフィールAPIテスト")
        response = client.get('/profile/ike3don3')
        if response.status_code == 200:
            profile_data = response.get_json()
            if profile_data and 'user' in profile_data:
                print("  プロフィール取得: OK")
                print(f"  ユーザー名: {profile_data['user']['name']}")
                print(f"  興味数: {len(profile_data.get('interests', []))}")
                print(f"  スキル数: {len(profile_data.get('skills', []))}")
        
        # 4. マッチングAPI のテスト
        print("✅ マッチングAPIテスト")
        response = client.get('/matches/ike3don3')
        if response.status_code == 200:
            matches_data = response.get_json()
            if matches_data and 'matches' in matches_data:
                print("  マッチング取得: OK")
                print(f"  マッチ候補数: {matches_data['total_matches']}")
                
                for i, match in enumerate(matches_data['matches'][:3], 1):
                    print(f"    {i}. {match['name']} (相性: {match['compatibility_score']:.3f})")
        
        # 5. 分析API のテスト（既存ユーザー）
        print("✅ 分析APIテスト")
        test_data = {"username": "ike3don3"}
        response = client.post('/analyze', 
                             data=json.dumps(test_data),
                             content_type='application/json')
        
        if response.status_code == 200:
            analysis_data = response.get_json()
            if analysis_data and 'matches' in analysis_data:
                print("  分析+マッチング: OK")
                print(f"  統合マッチ候補: {len(analysis_data['matches'])}件")
        
        print("🎉 統合Flaskアプリテスト完了")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """全APIエンドポイントのテスト"""
    print("\n🔗 APIエンドポイント一覧テスト")
    
    app.config['TESTING'] = True
    client = app.test_client()
    
    endpoints = [
        ('GET', '/', 'メインページ'),
        ('GET', '/matching', 'マッチングページ'),
        ('GET', '/profile/ike3don3', 'プロフィールAPI'),
        ('GET', '/matches/ike3don3', 'マッチングAPI'),
        ('POST', '/analyze', '分析API')
    ]
    
    print("エンドポイント一覧:")
    for method, path, description in endpoints:
        try:
            if method == 'GET':
                response = client.get(path)
            else:
                response = client.post(path, 
                                     data=json.dumps({"username": "ike3don3"}),
                                     content_type='application/json')
            
            status = "✅" if response.status_code == 200 else "❌"
            print(f"  {status} {method:4s} {path:20s} - {description} ({response.status_code})")
            
        except Exception as e:
            print(f"  ❌ {method:4s} {path:20s} - エラー: {e}")

if __name__ == "__main__":
    success = test_integrated_app()
    
    if success:
        test_api_endpoints()
    
    print("\n📋 統合テスト完了")
    print("🚀 アプリ起動: python app.py")
    print("🌐 メインページ: http://localhost:5002")
    print("🤝 マッチング: http://localhost:5002/matching")