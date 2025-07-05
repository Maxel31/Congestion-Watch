# ML実装詳細 
- 施設の混雑状況を時系列予測する回帰分類モデルを作成する。

# 入出力 
## 入力 
- 入力データはdatabase から受け取る。
- 入力データの形式は以下のとおり。

### databaseからモデルに渡す値
時刻tに対して、以下のデータの受け渡しを行うことを想定する。
#### 正解ラベル(任意の時刻での混雑度)
actual_score.score -> 時刻tにおける混雑度
#### 特徴量
actual_score.place_id -> 場所ID
actual_score.target_datetime -> 時刻t
actual_score.created_at -> 時刻tにおけるデータの作成日時

### モデルからdatabaseに返す値
時刻kに作成したモデルは、時刻m(>k)に対する予測として、以下の値をDBに返す。
(モデルは定期的に更新されるため)
prediction_score.model_id -> モデルID
prediction_score.score -> 時刻tに対する混雑度予測
prediction_score.place_id -> 場所ID
prediction_score.target_datetime -> 時刻m
prediction_score.created_at -> 時刻m対する混雑度予測データの作成日時
prediction_model.sensor_id -> センサーID
prediction_model.model_params -> モデルのパラメータ
prediction_model.created_at -> モデルの作成日時

# databaseの構造(参考)
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

# モデル 
RandomForestRegressor

# 追加情報
  1. 特徴量の詳細：
    - 過去何時間/何日分のデータを使用するか？
    サンプルデータを除く全データを学習に使用する。

    - 天気情報（weather）を特徴量として使用するか？
    今後、特徴量に追加するが、ひとまず使用しない方針で実装する。

    - 時間的特徴（曜日、時間帯、祝日等）を使用するか？
    今後、特徴量に追加するが、ひとまず使用しない方針で実装する。

    - 他の場所の混雑度を特徴量として使用するか？
    使用する。違いの施設の混雑度にはある程度相関があると考えられるため。

  2. 予測範囲：
    - 時間先まで予測するか？（例：1時間後、3時間後、24時間後）
    24時間後まで予測する。
    - 予測の時間間隔は？（例：30分ごと、1時間ごと）
    - 5minごとに予測
  3. モデル更新頻度：
    - モデルをどのくらいの頻度で再訓練するか？（例：毎日、毎週）
    1日ごと、毎日12時のタイミングで再訓練する
    - 訓練に使用するデータの期間は？（例：過去30日分）
    過去全てのデータを学習に使用する
  4. 混雑度スコアの範囲：
    - scoreの値域は？（例：0-100、1-5）
    当該施設内のデバイスの数を混雑度として近似するため、スケールなし、整数値。
  5. システム要件：
    - 予測のレスポンスタイム要件は？
    ひとまず設定しない。
    - モデルの精度目標は？
    ひとまず設定しない
  6. モデルに渡すデータの欠損について
    - データ取得デバイスの不具合によって、データが欠損する場合がある。モデルにランダムフォレストを使用しているため、欠損値についても対応できるはずだが、念のため留意すること。
  7. モデルの予測タイミングについて
    - モデルの予測も5minごとに行う(5minごとにモデルの予測を行うことで、最新のデータを使って予測を行える)