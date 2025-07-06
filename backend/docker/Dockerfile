FROM golang:1.24.2-alpine

WORKDIR /app

# gitとbashをインストール（airの依存関係）
RUN apk add --no-cache git bash

# airをインストール
RUN go install github.com/air-verse/air@latest

# 依存関係管理のためのファイルをコピー
COPY go.mod go.sum ./

# 依存関係のダウンロード
RUN go mod download

# アプリケーションのコードをコピー
COPY . .

# airでホットリロードを有効にして実行
CMD ["air", "-c", ".air.toml"]
