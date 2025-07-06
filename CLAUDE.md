## 作業を始める上での注意点

- 作業を始める前に、remote のgithubリポジトリと接続できているか確認してください。
- 作業完了後は、ruff・mypyによるチェックを徹底してください。
- 1つの作業が完了する度に、CI/CDによる品質チェック・gitへのpushを行って下さい。
- 必ずuvを使用してください。

## テストに関する規則
- testファイルの名称はtestから始めるようにしてください。また、testフォルダ以下に格納するようにしてください。

## Database設計
### 使用する技術 
- PostgreSQL 

### データベース詳細 
- predicted_score 
| Column       | Data Type | Description               |
| ------------ | --------- | ------------------------- |
| id           | int       | PK                        |
| model\_id    | int       | FK → prediction\_model.id |
| score        | int       |                           |
| place\_id    | int       | FK → place.id             |
| target\_date | date      |                           |
| created\_at  | date      |                           |

- prediction_model
| Column        | Data Type | Description    |
| ------------- | --------- | -------------- |
| id            | int       | PK             |
| sensor\_id    | int       | FK → sensor.id |
| model\_params | jsonb     |                |
| created\_at   | date      |                |

- sensor
| Column      | Data Type | Description   |
| ----------- | --------- | ------------- |
| id          | int       | PK            |
| place\_id   | int       | FK → place.id |
| created\_at | date      |               |

- actual_score
| Column       | Data Type | Description   |
| ------------ | --------- | ------------- |
| id           | int       | PK            |
| score        | int       |               |
| place\_id    | int       | FK → place.id |
| target\_date | date      |               |
| created\_at  | date      |               |

- place
| Column      | Data Type | Description |
| ----------- | --------- | ----------- |
| id          | int       | PK          |
| name        | str       |             |
| created\_at | date      |             |

- weather
| Column      | Data Type | Description |
| ----------- | --------- | ----------- |
| id          | int       | PK          |
| date        | date      |             |
| weather     | string    |             |
| created\_at | date      |             |

### 要件
- 指定した時間(default: 5分)ごとにml, backend, 外部APIの値をもとにDBの更新を行い、同時に要求されたタイミングでデータが取り出せるようにする。
- 天候に取得は以下のAPIを使用する

## Database初期化・Seeding方針

### 現在の状態（2025-07-04）
- サンプルデータの投入機能を実装済み
- `database/docker/01-init-database.sql`でテーブル定義とサンプルデータを投入
- 開発・テスト用途に適したリアルなサンプルデータを生成

### サンプルデータの内容
1. **場所データ**: 北館食堂、南館食堂、図書館、体育館
2. **実測スコアデータ**: 
   - 過去2日分のデータ（30分間隔）
   - 時間帯による変動パターンを考慮
   - 場所ごとに異なる混雑傾向
3. **予測スコアデータ**:
   - 過去データに基づく予測値
   - 未来24時間の予測データ
4. **天気データ**: 過去3日分と今後2日分の天気情報

### データ特徴
- **時間帯変動**: 食堂は昼食・夕食時に混雑、図書館は夜間に混雑
- **リアルな変動**: random()を使用した自然な変動
- **予測精度**: 実測値に±5程度の誤差を付けた予測値
- **季節性**: 現在日時基準の動的データ生成

### 実行方法
```bash
docker-compose up -d postgres
```
上記コマンドで自動的にサンプルデータまで投入される。