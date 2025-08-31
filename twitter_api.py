#!/usr/bin/env python3
"""
Twitter API v2 連携モジュール
"""
import os
import tweepy
import requests
from dotenv import load_dotenv
from typing import Dict, List, Optional

load_dotenv()

class TwitterAPI:
    def __init__(self):
        """Twitter API クライアントの初期化"""
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        
        if not self.bearer_token:
            print("⚠️ TWITTER_BEARER_TOKEN が設定されていません")
            print("📝 X Developer Portal でBearer Tokenを取得してください:")
            print("   https://developer.twitter.com/en/portal/dashboard")
            self.client = None
        else:
            try:
                self.client = tweepy.Client(bearer_token=self.bearer_token)
                print("✅ Twitter API クライアント初期化完了")
            except Exception as e:
                print(f"❌ Twitter API 初期化エラー: {e}")
                self.client = None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """ユーザー名からユーザー情報を取得"""
        if not self.client:
            return None
            
        try:
            # @マークを除去
            username = username.replace("@", "")
            
            # ユーザー情報を取得
            user = self.client.get_user(
                username=username,
                user_fields=[
                    'created_at', 'description', 'entities', 'id', 'location',
                    'name', 'pinned_tweet_id', 'profile_image_url', 'protected',
                    'public_metrics', 'url', 'username', 'verified'
                ]
            )
            
            if user.data:
                return {
                    'id': user.data.id,
                    'name': user.data.name,
                    'username': user.data.username,
                    'description': user.data.description or "",
                    'location': user.data.location or "",
                    'followers_count': user.data.public_metrics['followers_count'],
                    'following_count': user.data.public_metrics['following_count'],
                    'tweet_count': user.data.public_metrics['tweet_count'],
                    'profile_image_url': user.data.profile_image_url,
                    'verified': user.data.verified or False,
                    'created_at': user.data.created_at.isoformat() if user.data.created_at else None
                }
            else:
                print(f"❌ ユーザー @{username} が見つかりません")
                return None
                
        except tweepy.Unauthorized:
            print("❌ Twitter API 認証エラー: Bearer Tokenを確認してください")
            return None
        except tweepy.NotFound:
            print(f"❌ ユーザー @{username} が見つかりません")
            return None
        except Exception as e:
            print(f"❌ Twitter API エラー: {e}")
            return None
    
    def get_user_tweets(self, username: str, max_results: int = 10) -> List[Dict]:
        """ユーザーの最新ツイートを取得"""
        if not self.client:
            return []
            
        try:
            username = username.replace("@", "")
            
            # まずユーザーIDを取得
            user = self.client.get_user(username=username)
            if not user.data:
                return []
            
            user_id = user.data.id
            
            # ユーザーのツイートを取得
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=min(max_results, 100),  # API制限
                tweet_fields=['created_at', 'public_metrics', 'context_annotations', 'lang'],
                exclude=['retweets', 'replies']  # リツイートとリプライを除外
            )
            
            if tweets.data:
                return [
                    {
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                        'retweet_count': tweet.public_metrics['retweet_count'] if tweet.public_metrics else 0,
                        'like_count': tweet.public_metrics['like_count'] if tweet.public_metrics else 0,
                        'lang': tweet.lang
                    }
                    for tweet in tweets.data
                ]
            else:
                return []
                
        except Exception as e:
            print(f"❌ ツイート取得エラー: {e}")
            return []
    
    def get_full_user_data(self, username: str) -> Optional[Dict]:
        """ユーザーの完全な情報を取得（プロフィール + 最新ツイート）"""
        print(f"🔍 @{username} のデータを取得中...")
        
        # ユーザー基本情報を取得
        user_info = self.get_user_by_username(username)
        if not user_info:
            return None
        
        # 最新ツイートを取得
        tweets = self.get_user_tweets(username, max_results=20)
        
        # 結果をまとめる
        return {
            'user_info': user_info,
            'tweets': tweets,
            'tweet_text_combined': ' '.join([tweet['text'] for tweet in tweets[:10]])  # 分析用
        }

# テスト用の代替実装（API制限回避）
class MockTwitterAPI:
    """テスト用のモックAPI（実際のAPIが使えない場合）"""
    
    def get_full_user_data(self, username: str) -> Dict:
        """ユーザー名に応じたリアルなモックデータを返す"""
        print(f"🔍 @{username} のモックデータを生成中...")
        
        # ユーザー名に応じて異なるモックデータを生成
        mock_profiles = {
            'ike3don3': {
                'name': '池田 太郎',
                'description': '東京通信大学 情報マネジメント学部 3年生。Web開発とデータ分析に興味があります。Python, JavaScript勉強中 🐍 #東京通信大学 #プログラミング',
                'location': '東京都',
                'followers_count': 180,
                'following_count': 220,
                'tweet_count': 890,
                'tweets': [
                    'React Hooksの使い方がやっと理解できた！useEffectの依存配列の概念が重要だった。 #React #JavaScript #プログラミング',
                    '東京通信大学のデータベース設計の授業、実践的で面白い。SQLの最適化について学んでる。 #東京通信大学 #データベース',
                    'Pythonでデータ可視化の課題。matplotlibとseabornを使い分けるのがコツかな。統計の知識も必要だと実感。 #Python #データサイエンス',
                    'オンライン授業の良いところは、録画を何度も見返せること。理解が深まる。 #東京通信大学 #オンライン学習',
                    'GitHubでポートフォリオ作成中。就活に向けて準備しないと。 #GitHub #就活 #ポートフォリオ'
                ]
            },
            'default': {
                'name': f'田中 {username}',
                'description': '東京通信大学で学んでいます。プログラミングとAIに興味があります。 #東京通信大学 #プログラミング #AI',
                'location': '東京, 日本',
                'followers_count': 245,
                'following_count': 180,
                'tweet_count': 1250,
                'tweets': [
                    '今日はPythonの機械学習ライブラリについて勉強しました。scikit-learnの使い方がだんだん分かってきた！ #プログラミング #機械学習',
                    '東京通信大学のオンライン授業、思ったより集中できる。先生の説明も分かりやすい。 #東京通信大学 #オンライン学習',
                    'データサイエンスの課題が面白い。実際のデータを使って分析するのは楽しいな。統計学の重要性を実感。',
                    'AIの倫理について考える授業があった。技術だけでなく、社会への影響も重要だと思う。 #AI #倫理',
                    'プログラミングの課題でつまづいたけど、同級生に教えてもらって解決。オンラインでも助け合えるのがいい。'
                ]
            }
        }
        
        # ユーザー固有のプロフィールを取得（なければデフォルト）
        profile = mock_profiles.get(username, mock_profiles['default'])
        
        mock_data = {
            'user_info': {
                'id': f'{hash(username) % 1000000000}',
                'name': profile['name'],
                'username': username,
                'description': profile['description'],
                'location': profile['location'],
                'followers_count': profile['followers_count'],
                'following_count': profile['following_count'],
                'tweet_count': profile['tweet_count'],
                'verified': False,
                'created_at': '2020-01-15T10:30:00Z'
            },
            'tweets': [
                {
                    'id': f'{i+1000}',
                    'text': tweet,
                    'created_at': f'2024-08-{17-i:02d}T{9+i*2:02d}:00:00Z',
                    'retweet_count': (i+1) * 2,
                    'like_count': (i+1) * 4,
                    'lang': 'ja'
                }
                for i, tweet in enumerate(profile['tweets'])
            ]
        }
        
        # 分析用のテキスト結合（tweetsは文字列のリスト）
        mock_data['tweet_text_combined'] = ' '.join(profile['tweets'])
        
        return mock_data

def get_twitter_client():
    """Twitter API クライアントを取得"""
    api = TwitterAPI()
    
    # API が利用できない場合はモックを使用
    if not api.client:
        print("⚠️ 実際のTwitter APIが利用できません。モックデータを使用します。")
        return MockTwitterAPI()
    
    return api