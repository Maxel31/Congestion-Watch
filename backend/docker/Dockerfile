FROM golang:1.24.2-alpine

WORKDIR /app

# 依存関係管理のためのファイルをコピー
COPY backend/go.mod backend/go.sum ./

# 依存関係のダウンロード
RUN go mod download

# アプリケーションのコードをコピー
COPY backend/ ./

# アプリケーションのビルドと実行
CMD ["go", "run", "main.go"]
