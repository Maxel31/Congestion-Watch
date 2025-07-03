## 作業を始める上での注意点

- 作業を始める前に、remote のgithubリポジトリと接続できているか確認してください。
- 作業完了後は、ruff・mypyによるチェックを徹底してください。
- 1つの作業が完了する度に、CI/CDによる品質チェック・gitへのpushを行って下さい。

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
