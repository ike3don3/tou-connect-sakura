#!/usr/bin/env python3
"""
Gemini API Mock for development
"""

class GenerativeModel:
    def __init__(self, model_name):
        self.model_name = model_name
    
    def generate_content(self, prompt):
        class MockResponse:
            @property
            def text(self):
                # モック分析結果を返す
                return """
                分析結果（モックデータ）：
                
                【主要な興味分野】
                - プログラミング・開発
                - AI・機械学習
                - Web技術
                
                【技術スキル】
                - Python
                - JavaScript
                - データベース設計
                
                【学習スタイル】
                - 実践重視
                - コミュニティ学習
                
                【性格特性】
                - 協調性が高い
                - 新技術への関心
                - 継続学習意欲
                """
        
        return MockResponse()

def configure(api_key):
    """モック設定関数"""
    pass
