# Congestion Watch Database

リアルタイム混雑状況予測システムのデータベース構成

## 📋 目次

- [概要](#概要)
- [データベース設計](#データベース設計)
- [セットアップ](#セットアップ)
- [初期データ](#初期データ)
- [トラブルシューティング](#トラブルシューティング)

## 📊 概要

このディレクトリは、混雑状況予測システムのデータベーススキーマと初期データを管理します。Docker Composeにより、コンテナ起動時にデータベースの作成、テーブル定義、初期データ投入がすべて自動的に実行されます。

## 🗄️ データベース設計

### テーブル構成

#### **place** - 場所情報
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | 主キー |
| name | VARCHAR(255) | 場所名 |
| created_at | TIMESTAMP | 作成日時 |

#### **sensor** - センサー情報
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | 主キー |
| place_id | INTEGER | 場所ID (FK) |
| created_at | TIMESTAMP | 作成日時 |

#### **prediction_model** - 予測モデル
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | 主キー |
| sensor_id | INTEGER | センサーID (FK) |
| model_params | JSONB | モデルパラメータ |
| created_at | TIMESTAMP | 作成日時 |

#### **actual_score** - 実測混雑度
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | 主キー |
| score | INTEGER | 混雑度スコア |
| place_id | INTEGER | 場所ID (FK) |
| target_datetime | TIMESTAMP | 測定日時 |
| created_at | TIMESTAMP | 作成日時 |

#### **predicted_score** - 予測混雑度
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | 主キー |
| model_id | INTEGER | モデルID (FK) |
| score | INTEGER | 予測スコア |
| place_id | INTEGER | 場所ID (FK) |
| target_datetime | TIMESTAMP | 予測対象日時 |
| created_at | TIMESTAMP | 作成日時 |

#### **weather** - 天気情報
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | 主キー |
| datetime | TIMESTAMP | 日時 |
| weather | VARCHAR(255) | 天気情報 |
| created_at | TIMESTAMP | 作成日時 |

### ER図

```
place (1) ----< (n) sensor
place (1) ----< (n) actual_score
place (1) ----< (n) predicted_score
sensor (1) ----< (n) prediction_model
prediction_model (1) ----< (n) predicted_score
```

## 🚀 セットアップ

### 1. 環境変数の設定

```bash
# 環境変数ファイルを設定
cp .env.example .env

# .envファイルを編集して必要な値を設定
# 特に以下の値は必ず変更してください：
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=congestion_watch
POSTGRES_USER=congestion_user
POSTGRES_PASSWORD=secure_password

# API Keyも必要に応じて設定：
OPENWEATHER_API_KEY=your-actual-api-key
GOOGLE_MAPS_API_KEY=your-actual-api-key
```

### 2. データベース起動（完全自動）

**これだけで完了です！**

```bash
# PostgreSQLコンテナを起動（初回起動時に全自動初期化）
docker-compose up -d postgres
```

以下が自動的に実行されます：
- データベース`congestion_watch`の作成
- ユーザー`congestion_user`の作成と権限設定
- 全テーブルの作成
- インデックスの作成
- **サンプルデータの投入**

### 3. 動作確認

```bash
# データベースの状態を確認
uv run --frozen python database/src/view_database.py --all
```

## 🌱 初期データ

Docker Compose起動時に以下のサンプルデータが自動投入されます：

### 場所データ（4件）
- 北館食堂
- 南館食堂
- 図書館
- 体育館

### 実測スコアデータ
- 過去2日分のデータ（30分間隔）
- 時間帯による混雑パターンを考慮
- 各場所ごとに異なる傾向（食堂は昼・夕方、図書館は夜間が混雑）

### 予測スコアデータ
- 過去データに基づく予測値（実測値±5の誤差）
- 未来24時間の予測データ

### その他
- センサーデータ：各場所に1つずつ
- 予測モデル：各センサーに機械学習モデル設定
- 天気データ：過去3日分と今後2日分の天気情報

## 📁 ディレクトリ構成

```
database/
├── README.md                     # このファイル
├── config.py                     # データベース接続設定
├── docker/                       # Docker関連設定
│   └── 01-init-database.sql      # 統合初期化スクリプト
├── schema/                       # テーブル定義（参照用）
│   └── tables/                   # 各テーブルのSQL定義
└── src/                          # ユーティリティ
    ├── __init__.py               # パッケージ初期化
    └── view_database.py          # データベース内容表示ツール
```

## 📋 利用可能なコマンド

### データベース内容の確認

```bash
# 基本情報
uv run --frozen python database/src/view_database.py

# テーブル一覧とレコード数
uv run --frozen python database/src/view_database.py --tables

# 場所一覧
uv run --frozen python database/src/view_database.py --places

# 最近のスコア
uv run --frozen python database/src/view_database.py --scores 10

# 統計情報
uv run --frozen python database/src/view_database.py --stats

# すべての情報を表示
uv run --frozen python database/src/view_database.py --all
```

### 接続テスト

```bash
# 直接接続
PGPASSWORD=secure_password psql -h localhost -U congestion_user -d congestion_watch

# テーブル一覧確認
PGPASSWORD=secure_password psql -h localhost -U congestion_user -d congestion_watch -c "\dt"
```

## 🛠️ トラブルシューティング

### PostgreSQL接続エラー

```bash
# 1. コンテナが起動しているか確認
docker-compose ps

# 2. 環境変数の確認
echo $POSTGRES_PASSWORD

# 3. 接続テスト
PGPASSWORD=secure_password psql -h localhost -U congestion_user -d congestion_watch -c "SELECT 1;"
```

### データベースの再初期化

```bash
# コンテナとボリュームを完全削除
docker-compose down -v

# 再起動（自動的に再初期化される）
docker-compose up -d postgres
```

### ログの確認

```bash
# PostgreSQLのログを確認
docker-compose logs postgres

# 初期化ログの確認
docker-compose logs postgres | grep -i "init"
```

## 🔧 開発者向け情報

### カスタマイズ

初期データやテーブル定義を変更したい場合は、`docker/01-init-database.sql`を編集してください。変更後はコンテナを再起動する必要があります。

### データベースのバックアップ

```bash
# データベース全体のバックアップ
PGPASSWORD=secure_password pg_dump -h localhost -U congestion_user congestion_watch > backup.sql

# データのみバックアップ
PGPASSWORD=secure_password pg_dump -h localhost -U congestion_user --data-only congestion_watch > data_backup.sql
```

---

**作成日**: 2025-07-03  
**更新日**: 2025-07-04  
**バージョン**: 3.0.0