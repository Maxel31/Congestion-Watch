# Congestion Watch Database

リアルタイム混雑状況予測システムのデータベース機能

## 📋 目次

- [概要](#概要)
- [データベース設計](#データベース設計)
- [セットアップ](#セットアップ)
- [機能一覧](#機能一覧)
- [使い方](#使い方)
- [API連携](#api連携)
- [今後の実装予定](#今後の実装予定)
- [トラブルシューティング](#トラブルシューティング)

## 📊 概要

このデータベースシステムは、混雑状況の予測と分析を行うために以下の機能を提供します：

- **リアルタイムデータ取得**: Googleスプレッドシートから5分間隔でデータを自動取得
- **天気データ管理**: 外部APIからの天気情報の取得・保存
- **予測モデル管理**: 機械学習モデルとその予測結果の管理
- **データ可視化**: 蓄積されたデータの表示・分析機能

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
| target_date | DATE | 予測対象日 |
| created_at | TIMESTAMP | 作成日時 |

#### **weather** - 天気情報
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | 主キー |
| datetime | TIMESTAMP | 日時 |
| weather | VARCHAR(255) | 天気情報 |
| created_at | TIMESTAMP | 作成日時 |

## 🚀 セットアップ

### 1. 環境設定

```bash
# 環境変数ファイルを設定
cp config.env.example config.env

# 必要な環境変数を設定
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=congestion_watch_dev
POSTGRES_USER=congestion_user
POSTGRES_PASSWORD=secure_password

# スプレッドシート設定
SPREADSHEET_ID=1LUE3KlT_J1lSgYmclg-ljiXDS4JYaAwEtc0X-ia-twU
SPREADSHEET_GID=1986572533

# API設定
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
OPENWEATHER_API_KEY=your-openweather-api-key
WEATHER_LOCATION=Tokyo,JP
```

### 2. データベース起動

```bash
# PostgreSQLコンテナを起動
docker-compose --env-file config.env up -d postgres

# データベースの初期化
cd database/scripts
./setup_database.sh
```

### 3. 手動セットアップ（詳細制御）

```bash
# マイグレーション実行
./migrate.sh up

# 初期データ挿入
PGPASSWORD=secure_password psql -h localhost -U congestion_user -d congestion_watch_dev -f ../seeds/initial_data.sql

# スプレッドシートデータ取得（既存データ消去）
uv run python ../src/fetch_spreadsheet_data.py --clear
```

## ⚙️ 機能一覧

### データ取得・管理

#### **スプレッドシートデータ取得**
```bash
# 基本実行（追加挿入）
uv run python database/src/fetch_spreadsheet_data.py

# 既存データを消去してから挿入
uv run python database/src/fetch_spreadsheet_data.py --clear
```

#### **天気データ取得**
```bash
# 1回実行
OPENWEATHER_API_KEY=your-key uv run python database/src/weather_fetcher.py

# スケジューラー実行（60分間隔）
OPENWEATHER_API_KEY=your-key uv run python database/src/weather_scheduler.py

# カスタム間隔（30分間隔）
OPENWEATHER_API_KEY=your-key uv run python database/src/weather_scheduler.py --interval 30
```

#### **混雑度データスケジューラー**
```bash
# 5分間隔で自動実行
uv run python database/src/data_scheduler.py

# カスタム間隔（10分間隔）
uv run python database/src/data_scheduler.py --interval 10

# 1回だけ実行
uv run python database/src/data_scheduler.py --once
```

### データ表示・分析

#### **データベース内容表示**
```bash
# 環境変数を設定
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=congestion_user
export POSTGRES_PASSWORD=secure_password
export POSTGRES_DB=congestion_watch_dev

# テーブル一覧とレコード数
uv run python database/src/view_database.py --tables

# 場所一覧
uv run python database/src/view_database.py --places

# 最近のスコア（50件）
uv run python database/src/view_database.py --scores 50

# 統計情報
uv run python database/src/view_database.py --stats

# 時間別統計
uv run python database/src/view_database.py --hourly

# 特定日の統計
uv run python database/src/view_database.py --hourly --date 2025-07-03

# すべての情報を表示
uv run python database/src/view_database.py --all
```

## 🔗 API連携

### Google Spreadsheet API
- **目的**: リアルタイム混雑度データの取得
- **データ形式**: CSV形式での取得
- **更新頻度**: 5分間隔（設定可能）
- **データ例**:
  ```csv
  DateTime,Phone Count,Location
  2025-07-03 14:30:00,45,北館食堂
  2025-07-03 14:35:00,52,北館食堂
  ```

### OpenWeather API
- **目的**: 天気データの取得
- **API エンドポイント**: Current Weather Data API
- **更新頻度**: 60分間隔（設定可能）
- **取得データ**: 天気、気温、湿度、気圧、風速など

### Google Maps Platform API
- **目的**: 地理情報・位置情報の取得
- **用途**: 場所の座標取得、距離計算など
- **状況**: API キー設定済み（実装予定）

## 🔮 今後の実装予定

### 優先度: 高

#### **1. OpenWeather API の本格運用**
```bash
# 必要な設定
OPENWEATHER_API_KEY=your-actual-api-key

# 実装予定機能
- 実際の天気データ取得
- 天気データと混雑度の相関分析
- 天気予報データの取得・保存
```

#### **2. Google Maps Platform API 統合**
```bash
# 実装予定機能
- 場所の緯度経度取得
- 複数地点間の距離計算
- ジオコーディング機能
- 逆ジオコーディング機能
```

#### **3. データ分析機能の強化**
- 時系列データ分析
- 混雑パターンの可視化
- 曜日・時間帯別分析
- 季節性分析

### 優先度: 中

#### **4. パフォーマンス最適化**
```sql
-- 追加予定インデックス
CREATE INDEX idx_actual_score_datetime_place ON actual_score(target_datetime, place_id);
CREATE INDEX idx_weather_datetime_weather ON weather(datetime, weather);
```

#### **5. データバックアップ機能**
```bash
# 実装予定
- 自動バックアップスクリプト
- データ復旧機能
- 増分バックアップ
```

#### **6. 監視・アラート機能**
- データ取得失敗時のアラート
- 異常値検知
- システムヘルスチェック

### 優先度: 低

#### **7. 追加API連携**
- **Yahoo Weather API**: バックアップ天気データ
- **国土地理院API**: 詳細地図情報
- **交通情報API**: 周辺交通状況

#### **8. 機械学習モデル統合**
- 予測モデルの自動訓練
- モデル性能評価
- A/Bテスト機能

## 🛠️ トラブルシューティング

### よくある問題

#### **PostgreSQL接続エラー**
```bash
# 解決方法
1. コンテナが起動しているか確認
docker-compose ps

2. 環境変数の確認
echo $POSTGRES_PASSWORD

3. 接続テスト
PGPASSWORD=secure_password psql -h localhost -U congestion_user -d congestion_watch_dev -c "SELECT 1;"
```

#### **スプレッドシートデータ取得失敗**
```bash
# 確認事項
1. スプレッドシートが公開されているか
2. SPREADSHEET_IDとSPREADSHEET_GIDが正しいか
3. ネットワーク接続の確認

# テスト方法
curl "https://docs.google.com/spreadsheets/d/1LUE3KlT_J1lSgYmclg-ljiXDS4JYaAwEtc0X-ia-twU/export?format=csv&gid=1986572533"
```

#### **Weather API エラー**
```bash
# 確認事項
1. OPENWEATHER_API_KEYが有効か
2. API使用制限に達していないか
3. 地域名（WEATHER_LOCATION）が正しいか

# テスト方法
curl "https://api.openweathermap.org/data/2.5/weather?q=Tokyo,JP&appid=YOUR_API_KEY"
```

### ログの確認

```bash
# スケジューラーログ
tail -f data_scheduler.log
tail -f weather_scheduler.log

# データベースログ
docker-compose logs postgres
```

### データの整合性チェック

```sql
-- 孤立レコードの確認
SELECT s.id FROM sensor s LEFT JOIN place p ON s.place_id = p.id WHERE p.id IS NULL;
SELECT a.id FROM actual_score a LEFT JOIN place p ON a.place_id = p.id WHERE p.id IS NULL;

-- データ件数の確認
SELECT 
  'actual_score' as table_name, COUNT(*) as records 
FROM actual_score 
UNION ALL 
SELECT 'place', COUNT(*) FROM place 
ORDER BY records DESC;
```

## 📞 サポート

問題が発生した場合は、以下の情報を含めてお問い合わせください：

1. **エラーメッセージ**: 完全なエラーログ
2. **実行環境**: OS、Dockerバージョン等
3. **設定情報**: 環境変数（秘匿情報は除く）
4. **再現手順**: エラーが発生するまでの操作

---

**作成日**: 2025-07-03  
**更新日**: 2025-07-03  
**バージョン**: 1.0.0