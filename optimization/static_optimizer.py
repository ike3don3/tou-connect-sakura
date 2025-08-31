"""
StaticOptimizer - 静的ファイル最適化システム
画像圧縮、CSS/JS最小化、CDN統合、キャッシュ設定
"""
import os
import json
import hashlib
import logging
import mimetypes
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import gzip

try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False

try:
    from PIL import Image, ImageOpt
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cssmin
    CSSMIN_AVAILABLE = True
except ImportError:
    CSSMIN_AVAILABLE = False

try:
    import jsmin
    JSMIN_AVAILABLE = True
except ImportError:
    JSMIN_AVAILABLE = False


class ImageOptimizer:
    """画像最適化クラス"""
    
    def __init__(self, monitoring_manager=None):
        self.monitoring = monitoring_manager
        self.logger = logging.getLogger(__name__)
        
        # 最適化設定
        self.jpeg_quality = 85
        self.png_optimize = True
        self.webp_quality = 80
        self.max_width = 1920
        self.max_height = 1080
        
        # サポートされる画像形式
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
        
        if not PIL_AVAILABLE:
            self.logger.warning("PIL/Pillow not available, image optimization disabled")
    
    def optimize_image(self, input_path: str, output_path: str = None, 
                      format_override: str = None) -> Dict[str, Any]:
        """画像の最適化"""
        if not PIL_AVAILABLE:
            return {'error': 'PIL/Pillow not available'}
        
        try:
            input_file = Path(input_path)
            if not input_file.exists():
                return {'error': f'Input file not found: {input_path}'}
            
            if input_file.suffix.lower() not in self.supported_formats:
                return {'error': f'Unsupported format: {input_file.suffix}'}
            
            # 出力パスの決定
            if output_path is None:
                output_path = str(input_file.with_suffix('.optimized' + input_file.suffix))
            
            # 元ファイルサイズ
            original_size = input_file.stat().st_size
            
            # 画像を開く
            with Image.open(input_path) as img:
                # EXIF情報を保持
                exif = img.info.get('exif')
                
                # リサイズ（必要な場合）
                if img.width > self.max_width or img.height > self.max_height:
                    img.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)
                
                # フォーマット決定
                output_format = format_override or img.format or 'JPEG'
                
                # 最適化設定
                save_kwargs = {}
                
                if output_format.upper() == 'JPEG':
                    save_kwargs.update({
                        'quality': self.jpeg_quality,
                        'optimize': True,
                        'progressive': True
                    })
                    if exif:
                        save_kwargs['exif'] = exif
                
                elif output_format.upper() == 'PNG':
                    save_kwargs.update({
                        'optimize': self.png_optimize,
                        'compress_level': 9
                    })
                
                elif output_format.upper() == 'WEBP':
                    save_kwargs.update({
                        'quality': self.webp_quality,
                        'optimize': True,
                        'method': 6  # 最高品質の圧縮
                    })
                
                # 保存
                img.save(output_path, format=output_format, **save_kwargs)
            
            # 最適化後のファイルサイズ
            optimized_size = Path(output_path).stat().st_size
            compression_ratio = (original_size - optimized_size) / original_size * 100
            
            result = {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'original_size': original_size,
                'optimized_size': optimized_size,
                'compression_ratio': compression_ratio,
                'format': output_format
            }
            
            # 監視メトリクス記録
            if self.monitoring:
                self.monitoring.record_counter("optimization.images.processed", 1)
                self.monitoring.record_gauge("optimization.images.compression_ratio", compression_ratio)
                self.monitoring.record_gauge("optimization.images.size_reduction", original_size - optimized_size)
            
            self.logger.info(f"Image optimized: {compression_ratio:.1f}% reduction")
            return result
            
        except Exception as e:
            self.logger.error(f"Image optimization failed: {e}")
            return {'error': str(e)}
    
    def create_responsive_images(self, input_path: str, output_dir: str) -> Dict[str, Any]:
        """レスポンシブ画像の生成"""
        if not PIL_AVAILABLE:
            return {'error': 'PIL/Pillow not available'}
        
        try:
            input_file = Path(input_path)
            output_directory = Path(output_dir)
            output_directory.mkdir(parents=True, exist_ok=True)
            
            # レスポンシブサイズ設定
            sizes = {
                'small': (480, 320),    # モバイル
                'medium': (768, 512),   # タブレット
                'large': (1200, 800),   # デスクトップ
                'xlarge': (1920, 1280)  # 高解像度
            }
            
            results = {}
            
            with Image.open(input_path) as img:
                original_width, original_height = img.size
                
                for size_name, (max_width, max_height) in sizes.items():
                    # 元画像より大きいサイズはスキップ
                    if max_width >= original_width and max_height >= original_height:
                        continue
                    
                    # リサイズ
                    resized_img = img.copy()
                    resized_img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    
                    # 保存
                    output_filename = f"{input_file.stem}_{size_name}{input_file.suffix}"
                    output_path = output_directory / output_filename
                    
                    # 最適化して保存
                    optimization_result = self.optimize_image(
                        str(resized_img.filename) if hasattr(resized_img, 'filename') else input_path,
                        str(output_path)
                    )
                    
                    if optimization_result.get('success'):
                        results[size_name] = {
                            'path': str(output_path),
                            'width': resized_img.width,
                            'height': resized_img.height,
                            'size': output_path.stat().st_size
                        }
            
            return {'success': True, 'responsive_images': results}
            
        except Exception as e:
            self.logger.error(f"Responsive image creation failed: {e}")
            return {'error': str(e)}


class CSSOptimizer:
    """CSS最適化クラス"""
    
    def __init__(self, monitoring_manager=None):
        self.monitoring = monitoring_manager
        self.logger = logging.getLogger(__name__)
        
        if not CSSMIN_AVAILABLE:
            self.logger.warning("cssmin not available, CSS minification disabled")
    
    def minify_css(self, input_path: str, output_path: str = None) -> Dict[str, Any]:
        """CSSの最小化"""
        try:
            input_file = Path(input_path)
            if not input_file.exists():
                return {'error': f'Input file not found: {input_path}'}
            
            # 出力パスの決定
            if output_path is None:
                output_path = str(input_file.with_suffix('.min.css'))
            
            # ファイル読み込み
            with open(input_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            original_size = len(css_content.encode('utf-8'))
            
            # 最小化
            if CSSMIN_AVAILABLE:
                minified_css = cssmin.cssmin(css_content)
            else:
                # フォールバック: 基本的な最小化
                minified_css = self._basic_css_minify(css_content)
            
            # 保存
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(minified_css)
            
            minified_size = len(minified_css.encode('utf-8'))
            compression_ratio = (original_size - minified_size) / original_size * 100
            
            result = {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'original_size': original_size,
                'minified_size': minified_size,
                'compression_ratio': compression_ratio
            }
            
            # 監視メトリクス記録
            if self.monitoring:
                self.monitoring.record_counter("optimization.css.processed", 1)
                self.monitoring.record_gauge("optimization.css.compression_ratio", compression_ratio)
            
            self.logger.info(f"CSS minified: {compression_ratio:.1f}% reduction")
            return result
            
        except Exception as e:
            self.logger.error(f"CSS minification failed: {e}")
            return {'error': str(e)}
    
    def _basic_css_minify(self, css_content: str) -> str:
        """基本的なCSS最小化（フォールバック）"""
        import re
        
        # コメント削除
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # 不要な空白削除
        css_content = re.sub(r'\s+', ' ', css_content)
        css_content = re.sub(r';\s*}', '}', css_content)
        css_content = re.sub(r'{\s*', '{', css_content)
        css_content = re.sub(r'}\s*', '}', css_content)
        css_content = re.sub(r':\s*', ':', css_content)
        css_content = re.sub(r';\s*', ';', css_content)
        
        return css_content.strip()


class JSOptimizer:
    """JavaScript最適化クラス"""
    
    def __init__(self, monitoring_manager=None):
        self.monitoring = monitoring_manager
        self.logger = logging.getLogger(__name__)
        
        if not JSMIN_AVAILABLE:
            self.logger.warning("jsmin not available, JS minification disabled")
    
    def minify_js(self, input_path: str, output_path: str = None) -> Dict[str, Any]:
        """JavaScriptの最小化"""
        try:
            input_file = Path(input_path)
            if not input_file.exists():
                return {'error': f'Input file not found: {input_path}'}
            
            # 出力パスの決定
            if output_path is None:
                output_path = str(input_file.with_suffix('.min.js'))
            
            # ファイル読み込み
            with open(input_path, 'r', encoding='utf-8') as f:
                js_content = f.read()
            
            original_size = len(js_content.encode('utf-8'))
            
            # 最小化
            if JSMIN_AVAILABLE:
                minified_js = jsmin.jsmin(js_content)
            else:
                # フォールバック: 基本的な最小化
                minified_js = self._basic_js_minify(js_content)
            
            # 保存
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(minified_js)
            
            minified_size = len(minified_js.encode('utf-8'))
            compression_ratio = (original_size - minified_size) / original_size * 100
            
            result = {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'original_size': original_size,
                'minified_size': minified_size,
                'compression_ratio': compression_ratio
            }
            
            # 監視メトリクス記録
            if self.monitoring:
                self.monitoring.record_counter("optimization.js.processed", 1)
                self.monitoring.record_gauge("optimization.js.compression_ratio", compression_ratio)
            
            self.logger.info(f"JS minified: {compression_ratio:.1f}% reduction")
            return result
            
        except Exception as e:
            self.logger.error(f"JS minification failed: {e}")
            return {'error': str(e)}
    
    def _basic_js_minify(self, js_content: str) -> str:
        """基本的なJS最小化（フォールバック）"""
        import re
        
        # 単行コメント削除（文字列内は除く）
        js_content = re.sub(r'//.*$', '', js_content, flags=re.MULTILINE)
        
        # 複数行コメント削除
        js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
        
        # 不要な空白削除
        js_content = re.sub(r'\s+', ' ', js_content)
        js_content = re.sub(r';\s*', ';', js_content)
        js_content = re.sub(r'{\s*', '{', js_content)
        js_content = re.sub(r'}\s*', '}', js_content)
        
        return js_content.strip()


class CompressionManager:
    """圧縮管理クラス"""
    
    def __init__(self, monitoring_manager=None):
        self.monitoring = monitoring_manager
        self.logger = logging.getLogger(__name__)
    
    def compress_file(self, input_path: str, compression_type: str = 'gzip') -> Dict[str, Any]:
        """ファイルの圧縮"""
        try:
            input_file = Path(input_path)
            if not input_file.exists():
                return {'error': f'Input file not found: {input_path}'}
            
            # ファイル読み込み
            with open(input_path, 'rb') as f:
                content = f.read()
            
            original_size = len(content)
            
            # 圧縮
            if compression_type.lower() == 'gzip':
                compressed_content = gzip.compress(content, compresslevel=9)
                output_path = str(input_file) + '.gz'
            elif compression_type.lower() == 'brotli':
                if not BROTLI_AVAILABLE:
                    return {'error': 'Brotli compression not available'}
                compressed_content = brotli.compress(content, quality=11)
                output_path = str(input_file) + '.br'
            else:
                return {'error': f'Unsupported compression type: {compression_type}'}
            
            # 保存
            with open(output_path, 'wb') as f:
                f.write(compressed_content)
            
            compressed_size = len(compressed_content)
            compression_ratio = (original_size - compressed_size) / original_size * 100
            
            result = {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio,
                'compression_type': compression_type
            }
            
            # 監視メトリクス記録
            if self.monitoring:
                self.monitoring.record_counter(f"optimization.compression.{compression_type}", 1)
                self.monitoring.record_gauge(f"optimization.compression.{compression_type}.ratio", compression_ratio)
            
            self.logger.info(f"File compressed ({compression_type}): {compression_ratio:.1f}% reduction")
            return result
            
        except Exception as e:
            self.logger.error(f"File compression failed: {e}")
            return {'error': str(e)}


class CDNManager:
    """CDN統合管理クラス"""
    
    def __init__(self, cdn_config: Dict[str, Any] = None, monitoring_manager=None):
        self.monitoring = monitoring_manager
        self.logger = logging.getLogger(__name__)
        
        # CDN設定
        self.cdn_config = cdn_config or {}
        self.cdn_enabled = self.cdn_config.get('enabled', False)
        self.cdn_base_url = self.cdn_config.get('base_url', '')
        self.cdn_domains = self.cdn_config.get('domains', [])
        
        # キャッシュ設定
        self.cache_headers = {
            'images': {'max-age': 31536000, 'immutable': True},  # 1年
            'css': {'max-age': 31536000, 'immutable': True},     # 1年
            'js': {'max-age': 31536000, 'immutable': True},      # 1年
            'fonts': {'max-age': 31536000, 'immutable': True},   # 1年
            'html': {'max-age': 3600, 'must-revalidate': True}   # 1時間
        }
    
    def get_cdn_url(self, asset_path: str, asset_type: str = None) -> str:
        """CDN URLの生成"""
        if not self.cdn_enabled or not self.cdn_base_url:
            return asset_path
        
        try:
            # アセットタイプの自動判定
            if asset_type is None:
                asset_type = self._detect_asset_type(asset_path)
            
            # CDNドメインの選択（ラウンドロビン）
            if self.cdn_domains:
                domain_index = hash(asset_path) % len(self.cdn_domains)
                cdn_domain = self.cdn_domains[domain_index]
            else:
                cdn_domain = self.cdn_base_url
            
            # URLの構築
            cdn_url = f"{cdn_domain.rstrip('/')}/{asset_path.lstrip('/')}"
            
            # 監視メトリクス記録
            if self.monitoring:
                self.monitoring.record_counter("optimization.cdn.url_generated", 1, {'type': asset_type})
            
            return cdn_url
            
        except Exception as e:
            self.logger.error(f"CDN URL generation failed: {e}")
            return asset_path
    
    def get_cache_headers(self, asset_type: str) -> Dict[str, str]:
        """キャッシュヘッダーの取得"""
        cache_config = self.cache_headers.get(asset_type, self.cache_headers['html'])
        
        headers = {}
        
        if 'max-age' in cache_config:
            headers['Cache-Control'] = f"max-age={cache_config['max-age']}"
            
            if cache_config.get('immutable'):
                headers['Cache-Control'] += ', immutable'
            
            if cache_config.get('must-revalidate'):
                headers['Cache-Control'] += ', must-revalidate'
        
        # ETag生成
        headers['ETag'] = f'"{hash(asset_type)}"'
        
        return headers
    
    def _detect_asset_type(self, asset_path: str) -> str:
        """アセットタイプの自動判定"""
        extension = Path(asset_path).suffix.lower()
        
        if extension in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico'}:
            return 'images'
        elif extension in {'.css'}:
            return 'css'
        elif extension in {'.js'}:
            return 'js'
        elif extension in {'.woff', '.woff2', '.ttf', '.otf', '.eot'}:
            return 'fonts'
        elif extension in {'.html', '.htm'}:
            return 'html'
        else:
            return 'other'


class StaticOptimizer:
    """静的ファイル最適化統合管理"""
    
    def __init__(self, config: Dict[str, Any] = None, monitoring_manager=None):
        self.monitoring = monitoring_manager
        self.logger = logging.getLogger(__name__)
        
        # 設定
        self.config = config or {}
        self.optimization_enabled = self.config.get('enabled', True)
        self.output_dir = Path(self.config.get('output_dir', 'static/optimized'))
        
        # 各最適化コンポーネントの初期化
        self.image_optimizer = ImageOptimizer(monitoring_manager)
        self.css_optimizer = CSSOptimizer(monitoring_manager)
        self.js_optimizer = JSOptimizer(monitoring_manager)
        self.compression_manager = CompressionManager(monitoring_manager)
        self.cdn_manager = CDNManager(self.config.get('cdn', {}), monitoring_manager)
        
        # 出力ディレクトリの作成
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 最適化履歴
        self.optimization_history = []
    
    def optimize_directory(self, input_dir: str, file_patterns: List[str] = None) -> Dict[str, Any]:
        """ディレクトリ全体の最適化"""
        if not self.optimization_enabled:
            return {'message': 'Optimization disabled'}
        
        try:
            input_directory = Path(input_dir)
            if not input_directory.exists():
                return {'error': f'Input directory not found: {input_dir}'}
            
            # デフォルトパターン
            if file_patterns is None:
                file_patterns = ['*.css', '*.js', '*.jpg', '*.jpeg', '*.png', '*.gif']
            
            results = {
                'processed_files': [],
                'errors': [],
                'total_original_size': 0,
                'total_optimized_size': 0,
                'total_files': 0
            }
            
            # ファイルの検索と最適化
            for pattern in file_patterns:
                for file_path in input_directory.rglob(pattern):
                    if file_path.is_file():
                        result = self.optimize_file(str(file_path))
                        
                        if result.get('success'):
                            results['processed_files'].append(result)
                            results['total_original_size'] += result.get('original_size', 0)
                            results['total_optimized_size'] += result.get('optimized_size', 0)
                        else:
                            results['errors'].append({
                                'file': str(file_path),
                                'error': result.get('error', 'Unknown error')
                            })
                        
                        results['total_files'] += 1
            
            # 全体の圧縮率計算
            if results['total_original_size'] > 0:
                overall_compression = (
                    (results['total_original_size'] - results['total_optimized_size']) /
                    results['total_original_size'] * 100
                )
                results['overall_compression_ratio'] = overall_compression
            
            # 監視メトリクス記録
            if self.monitoring:
                self.monitoring.record_gauge("optimization.batch.files_processed", results['total_files'])
                self.monitoring.record_gauge("optimization.batch.compression_ratio", 
                                           results.get('overall_compression_ratio', 0))
            
            self.logger.info(f"Directory optimization completed: {results['total_files']} files processed")
            return results
            
        except Exception as e:
            self.logger.error(f"Directory optimization failed: {e}")
            return {'error': str(e)}
    
    def optimize_file(self, input_path: str) -> Dict[str, Any]:
        """単一ファイルの最適化"""
        try:
            file_path = Path(input_path)
            extension = file_path.suffix.lower()
            
            # ファイルタイプに応じた最適化
            if extension in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}:
                return self.image_optimizer.optimize_image(input_path)
            
            elif extension == '.css':
                return self.css_optimizer.minify_css(input_path)
            
            elif extension == '.js':
                return self.js_optimizer.minify_js(input_path)
            
            else:
                return {'error': f'Unsupported file type: {extension}'}
                
        except Exception as e:
            self.logger.error(f"File optimization failed: {e}")
            return {'error': str(e)}
    
    def create_asset_manifest(self, assets_dir: str) -> Dict[str, Any]:
        """アセットマニフェストの作成"""
        try:
            assets_directory = Path(assets_dir)
            manifest = {
                'version': datetime.now(timezone.utc).isoformat(),
                'assets': {},
                'cdn_config': {
                    'enabled': self.cdn_manager.cdn_enabled,
                    'base_url': self.cdn_manager.cdn_base_url
                }
            }
            
            # アセットファイルの検索
            for asset_file in assets_directory.rglob('*'):
                if asset_file.is_file():
                    relative_path = str(asset_file.relative_to(assets_directory))
                    
                    # ファイルハッシュの生成
                    with open(asset_file, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()[:8]
                    
                    # アセット情報
                    asset_info = {
                        'path': relative_path,
                        'hash': file_hash,
                        'size': asset_file.stat().st_size,
                        'type': self.cdn_manager._detect_asset_type(relative_path),
                        'cdn_url': self.cdn_manager.get_cdn_url(relative_path),
                        'cache_headers': self.cdn_manager.get_cache_headers(
                            self.cdn_manager._detect_asset_type(relative_path)
                        )
                    }
                    
                    manifest['assets'][relative_path] = asset_info
            
            # マニフェストファイルの保存
            manifest_path = self.output_dir / 'asset-manifest.json'
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Asset manifest created: {len(manifest['assets'])} assets")
            return {'success': True, 'manifest_path': str(manifest_path), 'assets_count': len(manifest['assets'])}
            
        except Exception as e:
            self.logger.error(f"Asset manifest creation failed: {e}")
            return {'error': str(e)}
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """最適化統計の取得"""
        try:
            stats = {
                'optimization_enabled': self.optimization_enabled,
                'output_directory': str(self.output_dir),
                'components': {
                    'image_optimizer': {
                        'available': PIL_AVAILABLE,
                        'formats_supported': list(self.image_optimizer.supported_formats)
                    },
                    'css_optimizer': {
                        'available': CSSMIN_AVAILABLE
                    },
                    'js_optimizer': {
                        'available': JSMIN_AVAILABLE
                    },
                    'cdn_manager': {
                        'enabled': self.cdn_manager.cdn_enabled,
                        'base_url': self.cdn_manager.cdn_base_url,
                        'domains_count': len(self.cdn_manager.cdn_domains)
                    }
                },
                'optimization_history_count': len(self.optimization_history)
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Stats generation failed: {e}")
            return {'error': str(e)}