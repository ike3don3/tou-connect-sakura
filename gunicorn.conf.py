"""
Gunicorn設定ファイル - 本番環境用WSGIサーバー設定
"""
import os
import multiprocessing

# サーバー設定
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2

# ログ設定
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')  # stdout
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')   # stderr
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# プロセス設定
preload_app = True
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = os.getenv('GUNICORN_USER')
group = os.getenv('GUNICORN_GROUP')

# セキュリティ設定
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# パフォーマンス設定
worker_tmp_dir = '/dev/shm'  # メモリファイルシステムを使用

def when_ready(server):
    """サーバー起動時の処理"""
    server.log.info("TOU Connect server is ready. Listening on: %s", bind)

def worker_int(worker):
    """ワーカープロセス中断時の処理"""
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    """ワーカープロセス作成前の処理"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """ワーカープロセス作成後の処理"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def worker_abort(worker):
    """ワーカープロセス異常終了時の処理"""
    worker.log.info("worker received SIGABRT signal")