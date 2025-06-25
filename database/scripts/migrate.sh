#!/bin/bash
# マイグレーションスクリプト
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

# 引数の処理
ACTION=${1:-up}
MIGRATION_FILE=${2:-""}

if [ "$ACTION" = "up" ]; then
    if [ -z "$MIGRATION_FILE" ]; then
        echo "すべてのupマイグレーションを実行中..."
        for file in ../migrations/*.up.sql; do
            if [ -f "$file" ]; then
                echo "実行中: $file"
                PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$file"
            fi
        done
    else
        echo "マイグレーション実行中: $MIGRATION_FILE"
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "../migrations/$MIGRATION_FILE"
    fi
elif [ "$ACTION" = "down" ]; then
    if [ -z "$MIGRATION_FILE" ]; then
        echo "最新のdownマイグレーションを実行中..."
        # 最新のdownファイルを逆順で実行
        for file in $(ls -r ../migrations/*.down.sql); do
            if [ -f "$file" ]; then
                echo "実行中: $file"
                PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$file"
                break
            fi
        done
    else
        echo "マイグレーション実行中: $MIGRATION_FILE"
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "../migrations/$MIGRATION_FILE"
    fi
else
    echo "使用法: $0 [up|down] [migration_file]"
    echo "例: $0 up 000001_init_schema.up.sql"
    echo "例: $0 down 000001_init_schema.down.sql"
    exit 1
fi

echo "マイグレーションが完了しました！"