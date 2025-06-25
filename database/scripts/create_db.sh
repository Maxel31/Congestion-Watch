#!/bin/bash
# データベース作成スクリプト
# 作成日: 2025-06-25

set -e

# 環境変数の読み込み
if [ -f "../../config.env" ]; then
    source ../../config.env
fi

# デフォルト値の設定
DB_HOST=${POSTGRES_HOST:-localhost}
DB_PORT=${POSTGRES_PORT:-5432}
DB_USER=${POSTGRES_USER:-postgres}
DB_PASSWORD=${POSTGRES_PASSWORD:-password}
DB_NAME=${POSTGRES_DB:-congestion_watch}

echo "データベース作成中..."
echo "ホスト: $DB_HOST:$DB_PORT"
echo "データベース名: $DB_NAME"

# データベースの作成
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "データベース $DB_NAME は既に存在します"

# スキーマの適用
echo "スキーマを適用中..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f ../schema/init.sql

# 初期データの挿入
echo "初期データを挿入中..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f ../seeds/initial_data.sql

echo "データベースセットアップが完了しました！"