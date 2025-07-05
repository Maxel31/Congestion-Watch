FROM golang:1.24.2-alpine

WORKDIR /app

# gitとbashをインストール（airの依存関係）
RUN apk add --no-cache git bash

# airをインストール
RUN go install github.com/air-verse/air@latest

# 依存関係管理のためのファイルをコピー
COPY backend/go.mod backend/go.sum ./

# 依存関係のダウンロード
RUN go mod download

# アプリケーションのコードをコピー
COPY backend/ ./

# airでホットリロードを有効にして実行
CMD ["air", "-c", ".air.toml"]
