FROM node:20-alpine

WORKDIR /app

# 依存関係インストール用のファイルをコピー
COPY frontend/package.json frontend/yarn.lock ./

# 依存関係のインストール
RUN yarn install

# アプリケーションのコードをコピー
COPY frontend/ ./

# 開発サーバーを起動
CMD ["yarn", "dev", "--host"]
