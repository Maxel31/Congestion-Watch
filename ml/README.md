# ML Service for Congestion Watch

混雑度予測のための機械学習サービス

## 概要

このサービスは、施設の混雑状況を時系列予測するRandomForestRegressorベースの回帰モデルを提供します。

## 主要機能

- **混雑度予測**: 指定した場所の5分間隔で24時間先までの混雑度を予測
- **モデル訓練**: 全場所のデータを使用してモデルを訓練
- **定期更新**: 毎日12時に自動的にモデルを再訓練
- **予測データ生成**: 5分ごとに全場所の予測データを生成・保存
- **スケジューラー管理**: 定期処理の開始/停止/状態確認

## アーキテクチャ

```
ml/
├── main.py              # FastAPIアプリケーション
├── src/                 # ソースコード
│   ├── database.py      # データベース接続・ORM
│   ├── feature_engineering.py  # 特徴量エンジニアリング
│   ├── model.py         # 機械学習モデル
│   └── scheduler.py     # 定期処理スケジューラー
├── test/                # テストコード
│   ├── test_ml.py       # ユニットテスト
│   └── test_database_connection.py  # 統合テスト
├── models/              # 学習済みモデル保存
├── config/              # 設定ファイル
├── docker/              # Docker設定
├── pyproject.toml       # Python依存関係（uv管理）
├── .env                 # ML専用環境変数
├── config.py            # 設定管理
└── run_tests.py         # テスト実行スクリプト
```

## API エンドポイント

### 基本エンドポイント

- `GET /` - サービス情報
- `GET /health` - ヘルスチェック

### 予測エンドポイント

- `POST /predict` - 混雑度予測
  ```json
  {
    "place_id": 1,
    "target_datetime": "2024-01-01T12:00:00",
    "hours_ahead": 24
  }
  ```

### 訓練エンドポイント

- `POST /train` - モデル訓練
  ```json
  {
    "test_size": 0.2
  }
  ```

### スケジューラーエンドポイント

- `GET /scheduler/status` - スケジューラー状態確認
- `POST /scheduler/start` - スケジューラー開始
- `POST /scheduler/stop` - スケジューラー停止

## 使用技術

- **機械学習**: scikit-learn (RandomForestRegressor)
- **API**: FastAPI
- **データベース**: PostgreSQL + SQLAlchemy
- **スケジューリング**: APScheduler
- **データ処理**: pandas, numpy

## 特徴量

現在実装されている特徴量：

1. **時間的特徴**
   - 時刻（hour, minute）
   - 曜日（day_of_week）
   - 日・月（day, month）

2. **過去の混雑度統計**
   - 直近1時間の統計（平均、最大、最小、標準偏差）
   - 直近3時間の統計（平均、最大）
   - 前日同時刻の平均
   - 1週間前同時刻の平均

3. **他場所の混雑度**
   - 他の場所の直近30分間の統計（平均、最大）

## 予測スケジュール

- **モデル更新**: 毎日12:00に全モデルを再訓練
- **予測生成**: 5分ごとに全場所の24時間先予測を生成
- **データクリーンアップ**: 1時間ごとに24時間前より古い予測データを削除

## 環境変数

- `DATABASE_URL`: PostgreSQLデータベース接続URL
- `ML_PORT`: サービスポート（デフォルト: 8001）
- `AUTO_START_SCHEDULER`: スケジューラー自動開始（デフォルト: true）

## 実行方法

### 開発環境での起動

```bash
# 依存関係のインストール（uvを使用）
uv sync

# データベース接続設定（.envファイルで設定済み）
# ml/.env ファイルを確認・編集してください

# アプリケーション起動
uv run python main.py
```

### Docker環境での起動

```bash
# プロジェクトルートから実行
docker-compose up -d ml
```

### テスト実行

```bash
# 全テスト実行（型チェック、リンティング、ユニット、統合）
uv run python run_tests.py

# ユニットテストのみ
uv run --frozen pytest test/test_ml.py -v

# 統合テスト（データベース接続テスト）
uv run python test/test_database_connection.py

# 型チェック
uv run --frozen mypy src/ --ignore-missing-imports

# リンティング
uv run --frozen ruff check src/ test/
```

## データベース構造

このサービスは以下のテーブルを使用します：

- `place` - 場所情報
- `sensor` - センサー情報  
- `actual_score` - 実測混雑度
- `predicted_score` - 予測混雑度
- `prediction_model` - 予測モデル情報
- `weather` - 天気情報（将来拡張予定）

## 動作確認

### 1. データベース接続確認

```bash
# 統合テストでデータベース接続を確認
python tests/test_database_connection.py
```

### 2. APIエンドポイント確認

```bash
# ヘルスチェック
curl http://localhost:8001/health

# モデル訓練
curl -X POST http://localhost:8001/train \
  -H "Content-Type: application/json" \
  -d '{"test_size": 0.2}'

# 予測実行
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "place_id": 1,
    "target_datetime": "2024-01-01T12:00:00",
    "hours_ahead": 24
  }'

# スケジューラー状態確認
curl http://localhost:8001/scheduler/status
```

### 3. 5分間隔予測の動作確認

スケジューラーが起動している場合、以下が設定間隔（デフォルト5分）ごとに自動実行されます：

- 全場所の24時間先予測データ生成
- 予測結果のデータベース保存
- 古い予測データのクリーンアップ

ログで動作状況を確認できます：

```bash
# Docker環境の場合
docker logs congestion-watch-ml-1

# 開発環境の場合
# コンソール出力でログを確認
```

## 設定管理

### 環境変数設定

ML サービス専用の設定は `ml/.env` ファイルで管理されます：

```bash
# データベース接続設定
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/congestion_watch

# MLサービス設定
ML_PORT=8001
ENV=development
AUTO_START_SCHEDULER=true

# ログレベル
LOG_LEVEL=INFO

# モデル設定
MODEL_DIR=models
MODEL_RETRAIN_HOUR=12
PREDICTION_INTERVAL_MINUTES=5

# テスト用設定
TEST_DATABASE_URL=sqlite:///test.db
```

### config.py による設定管理

設定は `config.py` で一元管理され、型安全な設定アクセスを提供します。

## 実装済み機能

✅ **データベース統合**
- PostgreSQL接続とSQLAlchemyORM
- 実測データ・予測データの読み書き
- モデル情報の永続化

✅ **機械学習パイプライン**
- RandomForestRegressorによる混雑度予測
- 特徴量エンジニアリング（時間特徴、過去統計、他場所相関）
- モデル評価とメトリクス計算

✅ **API サービス**
- FastAPIベースのREST API
- 予測・訓練・スケジューラー管理エンドポイント
- エラーハンドリングとロギング

✅ **定期処理**
- 毎日12時のモデル再訓練
- 5分ごとの予測データ生成
- 古いデータの自動クリーンアップ

✅ **テストカバレッジ**
- ユニットテスト（API、モデル、特徴量）
- 統合テスト（データベース接続、エンドツーエンド）
- 型チェック（mypy）とリンティング（ruff）

## 注意事項

- 欠損値は-1で埋められ、RandomForestで処理されます
- 予測値は負の値を0にクリップされます
- モデルファイルは`models/`ディレクトリに保存されます
- SQLiteはテスト用途のみ、本番環境ではPostgreSQLを使用してください
- 予測の精度はデータ量と質に依存します（最低10件の訓練データが必要）