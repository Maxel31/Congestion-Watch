#!/bin/bash
# Docker初期化スクリプト
# 作成日: 2025-06-25

set -e

echo "PostgreSQLデータベースを初期化しています..."

# スキーマの適用
echo "スキーマを適用中..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/init.sql

# 初期データの挿入
echo "初期データを挿入中..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/initial_data.sql

echo "データベース初期化が完了しました！"