#!/usr/bin/env python3
"""
TOU Connect データベース初期化スクリプト
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from database.database_manager import DatabaseManager

def main():
    """データベースを初期化"""
    print("🚀 TOU Connect データベース初期化開始")
    
    # 本番用データベースを作成
    db_path = "tou_connect.db"
    db = DatabaseManager(db_path)
    
    try:
        print("📊 データベース情報:")
        tables = db.get_all_tables()
        print(f"  作成されたテーブル数: {len(tables)}")
        for table in tables:
            print(f"    - {table}")
        
        print("\n🔧 テーブル構造確認:")
        for table in ['users', 'user_analysis', 'user_interests']:
            info = db.get_table_info(table)
            print(f"  {table}: {len(info)}カラム")
        
        print(f"\n✅ データベース初期化完了: {db_path}")
        print("📍 データベースファイルの場所:", os.path.abspath(db_path))
        
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        sys.exit(1)
    finally:
        db.close_connection()

if __name__ == "__main__":
    main()