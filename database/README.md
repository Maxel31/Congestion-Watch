# Congestion Watch Database

混雑度予測システムのデータベース設計とマイグレーション管理

## 概要

PostgreSQLを使用した混雑度予測データの管理システムです。
実測データと予測データの比較・分析が可能な構造になっています。

## データベース構造

### テーブル構成

1. **place** - 場所管理
   - 渋谷駅前、新宿駅前などの場所情報

2. **sensor** - センサー管理
   - 各場所に設置されたセンサー情報

3. **prediction_model** - 予測モデル管理
   - 各センサーの予測モデル設定（JSONパラメータ）

4. **actual_predictions_date** - 日付管理
   - 実測・予測データの日付統一管理

5. **actual_score** - 実測スコア
   - センサーから取得した実際の混雑度データ

6. **predicted_score** - 予測スコア
   - モデルによる予測混雑度データ

7. **actual_predictions** - 実測・予測関連
   - 実測と予測の対応関係

詳細な構造は `docs/DB_abstract.png` を参照してください。

## ディレクトリ構造

```
database/
├── README.md               # このファイル
├── config.py              # データベース接続設定
├── docs/                  # ドキュメント
│   ├── CLAUDE.md         # 作業指示書
│   └── DB_abstract.png   # データベース構造図
├── docker/               # Docker関連
│   └── init-db.sh        # コンテナ初期化スクリプト
├── migrations/           # マイグレーション
│   ├── 000001_init_schema.up.sql
│   └── 000001_init_schema.down.sql
├── schema/               # スキーマ定義
│   ├── init.sql          # 統合初期化スクリプト
│   └── tables/           # 個別テーブル定義
│       ├── place.sql
│       ├── sensor.sql
│       ├── prediction_model.sql
│       ├── actual_predictions_date.sql
│       ├── actual_score.sql
│       ├── predicted_score.sql
│       └── actual_predictions.sql
├── scripts/              # 管理用スクリプト
│   ├── create_db.sh      # データベース作成
│   └── migrate.sh        # マイグレーション実行
└── seeds/                # 初期データ
    └── initial_data.sql  # サンプルデータ
```

## セットアップ

### 1. Docker Composeを使用（推奨）

```bash
# データベースを起動
docker-compose up db

# 別ターミナルで確認
docker-compose exec db psql -U congestion_user -d congestion_watch -c "\dt"
```

### 2. ローカルPostgreSQLを使用

```bash
# 環境変数を設定
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=congestion_user
export POSTGRES_PASSWORD=secure_password
export POSTGRES_DB=congestion_watch

# データベース作成
cd database/scripts
./create_db.sh
```

## マイグレーション

### アップマイグレーション（スキーマ適用）

```bash
cd database/scripts
./migrate.sh up
```

### ダウンマイグレーション（スキーマ削除）

```bash
cd database/scripts
./migrate.sh down
```

### 特定のマイグレーション実行

```bash
cd database/scripts
./migrate.sh up 000001_init_schema.up.sql
./migrate.sh down 000001_init_schema.down.sql
```

## 設定

### 環境変数

以下の環境変数で接続設定をカスタマイズできます：

- `POSTGRES_HOST`: データベースホスト（デフォルト: localhost）
- `POSTGRES_PORT`: ポート番号（デフォルト: 5432）
- `POSTGRES_USER`: ユーザー名（デフォルト: congestion_user）
- `POSTGRES_PASSWORD`: パスワード（デフォルト: secure_password）
- `POSTGRES_DB`: データベース名（デフォルト: congestion_watch）

### Python接続例

```python
from database.config import get_database_config, DatabaseConnectionManager

# 設定取得
config = get_database_config()
print(config.connection_string)

# 接続管理
manager = DatabaseConnectionManager()
connection_string = manager.get_connection_string()
```

## 開発ワークフロー

1. **ブランチ作成**: `feature/DB` ブランチで作業
2. **スキーマ変更**: `migrations/` にマイグレーションファイルを追加
3. **テスト**: Docker Composeでローカル動作確認
4. **CI/CD**: 品質チェック通過後にmainにマージ

## 注意事項

- データベース以外の構造は変更しないでください
- マイグレーションファイルは番号順で命名してください
- 本番環境のデータベースパスワードは適切に管理してください