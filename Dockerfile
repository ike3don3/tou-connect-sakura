# TOU Connect 本番環境用 Dockerfile

FROM python:3.11-slim

# メンテナ情報
LABEL maintainer="TOU Connect Team <admin@touconnect.com>"
LABEL version="1.0.0"
LABEL description="TOU Connect - 東京通信大学 学友マッチングプラットフォーム"

# 環境変数設定
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# システムパッケージ更新とインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    redis-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ設定
WORKDIR /app

# 依存関係ファイルコピー
COPY requirements-production.txt requirements.txt ./

# Python依存関係インストール
RUN pip install --upgrade pip && \
    pip install -r requirements-production.txt

# アプリケーションファイルコピー
COPY . .

# 非rootユーザー作成
RUN groupadd -r touconnect && \
    useradd -r -g touconnect -d /app -s /bin/bash touconnect && \
    chown -R touconnect:touconnect /app

# ポート公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ユーザー切り替え
USER touconnect

# エントリーポイント
ENTRYPOINT ["./docker-entrypoint.sh"]

# デフォルトコマンド
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app_launch:app"]
