#!/usr/bin/env python3
"""
静的ファイル最適化システムのテスト
StaticOptimizerの機能テスト
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from optimization.static_optimizer import StaticOptimizer, ImageOptimizer, CSSOptimizer, JSOptimizer, CDNManager
from monitoring.monitoring_manager import MonitoringManager
from database.database_manager import DatabaseManager


def create_test_files(test_dir: Path):
    """テスト用ファイルの作成"""
    # CSS テストファイル
    css_content = """
    /* This is a test CSS file */
    body {
        margin: 0;
        padding: 20px;
        font-family: Arial, sans-serif;
        background-color: #f0f0f0;
    }
    
    .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 15px;
    }
    
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
    }
    """
    
    css_file = test_dir / "test.css"
    css_file.write_text(css_content, encoding='utf-8')
    
    # JavaScript テストファイル
    js_content = """
    // This is a test JavaScript file
    function initializeApp() {
        console.log('Initializing application...');
        
        // Event listeners
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded');
            setupEventHandlers();
        });
        
        function setupEventHandlers() {
            const buttons = document.querySelectorAll('.btn');
            buttons.forEach(button => {
                button.addEventListener('click', handleButtonClick);
            });
        }
        
        function handleButtonClick(event) {
            event.preventDefault();
            console.log('Button clicked:', event.target);
        }
    }
    
    // Initialize the app
    initializeApp();
    """
    
    js_file = test_dir / "test.js"
    js_file.write_text(js_content, encoding='utf-8')
    
    # HTML テストファイル
    html_content = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test Page</title>
        <link rel="stylesheet" href="test.css">
    </head>
    <body>
        <div class="container">
            <header class="header">
                <h1>Test Page</h1>
            </header>
            <main>
                <p>This is a test page for optimization.</p>
                <button class="btn">Click me</button>
            </main>
        </div>
        <script src="test.js"></script>
    </body>
    </html>
    """
    
    html_file = test_dir / "test.html"
    html_file.write_text(html_content, encoding='utf-8')
    
    return {
        'css': str(css_file),
        'js': str(js_file),
        'html': str(html_file)
    }


def test_css_optimizer():
    """CSS最適化のテスト"""
    print("=== CSS最適化テスト ===")
    
    # MonitoringManagerの初期化
    db = DatabaseManager()
    monitoring = MonitoringManager(db)
    
    # CSS最適化の初期化
    css_optimizer = CSSOptimizer(monitoring)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)
            test_files = create_test_files(test_dir)
            
            # CSS最小化テスト
            print("1. CSS最小化テスト")
            
            result = css_optimizer.minify_css(test_files['css'])
            
            if result.get('success'):
                print(f"✓ CSS最小化成功:")
                print(f"  - 元サイズ: {result['original_size']} bytes")
                print(f"  - 最小化後: {result['minified_size']} bytes")
                print(f"  - 圧縮率: {result['compression_ratio']:.1f}%")
                
                # 最小化されたファイルの確認
                minified_file = Path(result['output_path'])
                assert minified_file.exists(), "最小化ファイルが作成されていない"
                
                with open(result['output_path'], 'r', encoding='utf-8') as f:
                    minified_content = f.read()
                
                # 最小化の確認（コメントが削除されているか）
                assert '/*' not in minified_content, "コメントが削除されていない"
                assert 'body{' in minified_content or 'body {' in minified_content, "CSSが正しく最小化されていない"
                
                print("✓ CSS最小化内容確認成功")
            else:
                print(f"❌ CSS最小化失敗: {result.get('error')}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ CSS最適化テストエラー: {e}")
        return False
    
    finally:
        monitoring.stop_background_tasks()


def test_js_optimizer():
    """JavaScript最適化のテスト"""
    print("\n=== JavaScript最適化テスト ===")
    
    # MonitoringManagerの初期化
    db = DatabaseManager()
    monitoring = MonitoringManager(db)
    
    # JS最適化の初期化
    js_optimizer = JSOptimizer(monitoring)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)
            test_files = create_test_files(test_dir)
            
            # JS最小化テスト
            print("1. JavaScript最小化テスト")
            
            result = js_optimizer.minify_js(test_files['js'])
            
            if result.get('success'):
                print(f"✓ JS最小化成功:")
                print(f"  - 元サイズ: {result['original_size']} bytes")
                print(f"  - 最小化後: {result['minified_size']} bytes")
                print(f"  - 圧縮率: {result['compression_ratio']:.1f}%")
                
                # 最小化されたファイルの確認
                minified_file = Path(result['output_path'])
                assert minified_file.exists(), "最小化ファイルが作成されていない"
                
                with open(result['output_path'], 'r', encoding='utf-8') as f:
                    minified_content = f.read()
                
                # 最小化の確認（コメントが削除されているか）
                assert '//' not in minified_content or 'http://' in minified_content, "単行コメントが削除されていない"
                assert 'function initializeApp' in minified_content, "JSが正しく最小化されていない"
                
                print("✓ JS最小化内容確認成功")
            else:
                print(f"❌ JS最小化失敗: {result.get('error')}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ JS最適化テストエラー: {e}")
        return False
    
    finally:
        monitoring.stop_background_tasks()


def test_cdn_manager():
    """CDN管理のテスト"""
    print("\n=== CDN管理テスト ===")
    
    # MonitoringManagerの初期化
    db = DatabaseManager()
    monitoring = MonitoringManager(db)
    
    try:
        # CDN設定
        cdn_config = {
            'enabled': True,
            'base_url': 'https://cdn.example.com',
            'domains': [
                'https://cdn1.example.com',
                'https://cdn2.example.com',
                'https://cdn3.example.com'
            ]
        }
        
        cdn_manager = CDNManager(cdn_config, monitoring)
        
        # 1. CDN URL生成テスト
        print("1. CDN URL生成テスト")
        
        test_assets = [
            ('static/css/style.css', 'css'),
            ('static/js/app.js', 'js'),
            ('static/images/logo.png', 'images'),
            ('static/fonts/font.woff2', 'fonts')
        ]
        
        for asset_path, expected_type in test_assets:
            cdn_url = cdn_manager.get_cdn_url(asset_path)
            detected_type = cdn_manager._detect_asset_type(asset_path)
            
            assert cdn_url.startswith('https://cdn'), f"CDN URLが正しく生成されていない: {cdn_url}"
            assert detected_type == expected_type, f"アセットタイプ検出エラー: expected {expected_type}, got {detected_type}"
            
            print(f"✓ {asset_path} -> {cdn_url} ({detected_type})")
        
        # 2. キャッシュヘッダー生成テスト
        print("2. キャッシュヘッダー生成テスト")
        
        for asset_type in ['css', 'js', 'images', 'fonts', 'html']:
            headers = cdn_manager.get_cache_headers(asset_type)
            
            assert 'Cache-Control' in headers, f"{asset_type}のCache-Controlヘッダーが生成されていない"
            assert 'ETag' in headers, f"{asset_type}のETagヘッダーが生成されていない"
            
            print(f"✓ {asset_type}: {headers['Cache-Control']}")
        
        # 3. CDN無効時のテスト
        print("3. CDN無効時のテスト")
        
        cdn_config_disabled = {'enabled': False}
        cdn_manager_disabled = CDNManager(cdn_config_disabled, monitoring)
        
        original_path = 'static/css/style.css'
        cdn_url_disabled = cdn_manager_disabled.get_cdn_url(original_path)
        
        assert cdn_url_disabled == original_path, "CDN無効時に元のパスが返されていない"
        print(f"✓ CDN無効時: {original_path} -> {cdn_url_disabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ CDN管理テストエラー: {e}")
        return False
    
    finally:
        monitoring.stop_background_tasks()


def test_static_optimizer():
    """StaticOptimizer統合テスト"""
    print("\n=== StaticOptimizer統合テスト ===")
    
    # MonitoringManagerの初期化
    db = DatabaseManager()
    monitoring = MonitoringManager(db)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)
            test_files = create_test_files(test_dir)
            
            # StaticOptimizerの初期化
            config = {
                'enabled': True,
                'output_dir': str(test_dir / 'optimized'),
                'cdn': {
                    'enabled': True,
                    'base_url': 'https://cdn.example.com',
                    'domains': ['https://cdn1.example.com', 'https://cdn2.example.com']
                }
            }
            
            optimizer = StaticOptimizer(config, monitoring)
            
            # 1. 単一ファイル最適化テスト
            print("1. 単一ファイル最適化テスト")
            
            css_result = optimizer.optimize_file(test_files['css'])
            js_result = optimizer.optimize_file(test_files['js'])
            
            assert css_result.get('success'), f"CSS最適化失敗: {css_result.get('error')}"
            assert js_result.get('success'), f"JS最適化失敗: {js_result.get('error')}"
            
            print(f"✓ CSS最適化: {css_result['compression_ratio']:.1f}% 削減")
            print(f"✓ JS最適化: {js_result['compression_ratio']:.1f}% 削減")
            
            # 2. ディレクトリ最適化テスト
            print("2. ディレクトリ最適化テスト")
            
            dir_result = optimizer.optimize_directory(str(test_dir), ['*.css', '*.js'])
            
            assert 'processed_files' in dir_result, "ディレクトリ最適化結果が不正"
            assert len(dir_result['processed_files']) >= 2, "処理されたファイル数が不足"
            
            print(f"✓ ディレクトリ最適化完了:")
            print(f"  - 処理ファイル数: {dir_result['total_files']}")
            print(f"  - 成功ファイル数: {len(dir_result['processed_files'])}")
            print(f"  - エラー数: {len(dir_result['errors'])}")
            
            if 'overall_compression_ratio' in dir_result:
                print(f"  - 全体圧縮率: {dir_result['overall_compression_ratio']:.1f}%")
            
            # 3. アセットマニフェスト作成テスト
            print("3. アセットマニフェスト作成テスト")
            
            manifest_result = optimizer.create_asset_manifest(str(test_dir))
            
            assert manifest_result.get('success'), f"マニフェスト作成失敗: {manifest_result.get('error')}"
            
            manifest_path = Path(manifest_result['manifest_path'])
            assert manifest_path.exists(), "マニフェストファイルが作成されていない"
            
            print(f"✓ アセットマニフェスト作成成功:")
            print(f"  - マニフェストパス: {manifest_result['manifest_path']}")
            print(f"  - アセット数: {manifest_result['assets_count']}")
            
            # マニフェスト内容の確認
            import json
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            
            assert 'version' in manifest_data, "マニフェストにバージョン情報がない"
            assert 'assets' in manifest_data, "マニフェストにアセット情報がない"
            assert len(manifest_data['assets']) > 0, "アセット情報が空"
            
            print("✓ マニフェスト内容確認成功")
            
            # 4. 最適化統計テスト
            print("4. 最適化統計テスト")
            
            stats = optimizer.get_optimization_stats()
            
            assert 'optimization_enabled' in stats, "統計に最適化有効フラグがない"
            assert 'components' in stats, "統計にコンポーネント情報がない"
            
            print("✓ 最適化統計取得成功:")
            print(f"  - 最適化有効: {stats['optimization_enabled']}")
            print(f"  - 出力ディレクトリ: {stats['output_directory']}")
            print(f"  - CDN有効: {stats['components']['cdn_manager']['enabled']}")
            
            return True
        
    except Exception as e:
        print(f"❌ StaticOptimizer統合テストエラー: {e}")
        return False
    
    finally:
        monitoring.stop_background_tasks()


def test_compression():
    """圧縮機能のテスト"""
    print("\n=== 圧縮機能テスト ===")
    
    # MonitoringManagerの初期化
    db = DatabaseManager()
    monitoring = MonitoringManager(db)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)
            
            # テストファイルの作成
            test_content = "This is a test file for compression. " * 100  # 繰り返しで圧縮効果を高める
            test_file = test_dir / "test.txt"
            test_file.write_text(test_content, encoding='utf-8')
            
            # StaticOptimizerの初期化
            config = {'enabled': True, 'output_dir': str(test_dir / 'compressed')}
            optimizer = StaticOptimizer(config, monitoring)
            
            # 1. Gzip圧縮テスト
            print("1. Gzip圧縮テスト")
            
            gzip_result = optimizer.compression_manager.compress_file(str(test_file), 'gzip')
            
            if gzip_result.get('success'):
                print(f"✓ Gzip圧縮成功:")
                print(f"  - 元サイズ: {gzip_result['original_size']} bytes")
                print(f"  - 圧縮後: {gzip_result['compressed_size']} bytes")
                print(f"  - 圧縮率: {gzip_result['compression_ratio']:.1f}%")
                
                # 圧縮ファイルの確認
                compressed_file = Path(gzip_result['output_path'])
                assert compressed_file.exists(), "Gzip圧縮ファイルが作成されていない"
                assert compressed_file.suffix == '.gz', "Gzip拡張子が正しくない"
            else:
                print(f"❌ Gzip圧縮失敗: {gzip_result.get('error')}")
                return False
            
            # 2. Brotli圧縮テスト
            print("2. Brotli圧縮テスト")
            
            brotli_result = optimizer.compression_manager.compress_file(str(test_file), 'brotli')
            
            if brotli_result.get('success'):
                print(f"✓ Brotli圧縮成功:")
                print(f"  - 元サイズ: {brotli_result['original_size']} bytes")
                print(f"  - 圧縮後: {brotli_result['compressed_size']} bytes")
                print(f"  - 圧縮率: {brotli_result['compression_ratio']:.1f}%")
                
                # 圧縮ファイルの確認
                compressed_file = Path(brotli_result['output_path'])
                assert compressed_file.exists(), "Brotli圧縮ファイルが作成されていない"
                assert compressed_file.suffix == '.br', "Brotli拡張子が正しくない"
            else:
                # Brotliが利用できない場合はスキップ
                if 'not available' in brotli_result.get('error', ''):
                    print("⚠️ Brotli圧縮スキップ: ライブラリが利用できません")
                else:
                    print(f"❌ Brotli圧縮失敗: {brotli_result.get('error')}")
                    return False
            
            return True
        
    except Exception as e:
        print(f"❌ 圧縮機能テストエラー: {e}")
        return False
    
    finally:
        monitoring.stop_background_tasks()


def main():
    """メインテスト実行"""
    print("静的ファイル最適化システムテスト開始")
    print("=" * 50)
    
    results = []
    
    # 各テストの実行
    results.append(("CSS最適化", test_css_optimizer()))
    results.append(("JavaScript最適化", test_js_optimizer()))
    results.append(("CDN管理", test_cdn_manager()))
    results.append(("StaticOptimizer統合", test_static_optimizer()))
    results.append(("圧縮機能", test_compression()))
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("テスト結果サマリー")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n総合結果: {passed}/{total} テスト通過")
    
    if passed == total:
        print("🎉 全てのテストが成功しました！")
        return True
    else:
        print("⚠️  一部のテストが失敗しました。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)