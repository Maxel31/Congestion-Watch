-- マイグレーション: 初期スキーマ作成
-- 作成日: 2025-06-25
-- バージョン: 000001

-- 場所テーブル
CREATE TABLE place (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- センサーテーブル
CREATE TABLE sensor (
    id SERIAL PRIMARY KEY,
    place_id INTEGER NOT NULL REFERENCES place(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 予測モデルテーブル
CREATE TABLE prediction_model (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES sensor(id) ON DELETE CASCADE,
    model_params JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 実測スコアテーブル
CREATE TABLE actual_score (
    id SERIAL PRIMARY KEY,
    score INTEGER NOT NULL,
    place_id INTEGER NOT NULL REFERENCES place(id) ON DELETE CASCADE,
    target_datetime TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 予測スコアテーブル
CREATE TABLE predicted_score (
    id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES prediction_model(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    place_id INTEGER NOT NULL REFERENCES place(id) ON DELETE CASCADE,
    target_datetime TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 天候テーブル
CREATE TABLE weather (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP NOT NULL,
    weather VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- インデックスの作成
CREATE INDEX idx_sensor_place_id ON sensor(place_id);
CREATE INDEX idx_prediction_model_sensor_id ON prediction_model(sensor_id);
CREATE INDEX idx_actual_score_place_id ON actual_score(place_id);
CREATE INDEX idx_actual_score_target_datetime ON actual_score(target_datetime);
CREATE INDEX idx_predicted_score_model_id ON predicted_score(model_id);
CREATE INDEX idx_predicted_score_place_id ON predicted_score(place_id);
CREATE INDEX idx_predicted_score_target_datetime ON predicted_score(target_datetime);
CREATE INDEX idx_weather_datetime ON weather(datetime);