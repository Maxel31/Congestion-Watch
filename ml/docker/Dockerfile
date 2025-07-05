FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# アプリケーションのコードをコピー
COPY ml/ ./

# アプリケーションの実行
CMD ["python", "main.py"]
