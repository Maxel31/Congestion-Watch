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
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 予測モデルテーブル
CREATE TABLE prediction_model (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES sensor(id) ON DELETE CASCADE,
    model_params JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 実測・予測日付テーブル
CREATE TABLE actual_predictions_date (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date)
);

-- 実測スコアテーブル
CREATE TABLE actual_score (
    id SERIAL PRIMARY KEY,
    score INTEGER NOT NULL,
    measured_date_id INTEGER NOT NULL REFERENCES actual_predictions_date(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 予測スコアテーブル
CREATE TABLE predicted_score (
    id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES prediction_model(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    target_date_id INTEGER NOT NULL REFERENCES actual_predictions_date(id) ON DELETE CASCADE,
    predicted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 実測・予測関連テーブル
CREATE TABLE actual_predictions (
    id SERIAL PRIMARY KEY,
    actual_score_id INTEGER NOT NULL REFERENCES actual_score(id) ON DELETE CASCADE,
    predicted_score_id INTEGER NOT NULL REFERENCES predicted_score(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(actual_score_id, predicted_score_id)
);

-- 天候データテーブル
CREATE TABLE weather_data (
    id SERIAL PRIMARY KEY,
    date_id INTEGER NOT NULL REFERENCES actual_predictions_date(id) ON DELETE CASCADE,
    temperature DECIMAL(5,2),  -- 気温（摂氏）
    humidity INTEGER,          -- 湿度（%）
    precipitation DECIMAL(6,2), -- 降水量（mm）
    wind_speed DECIMAL(5,2),   -- 風速（m/s）
    weather_condition VARCHAR(100), -- 天候状況（晴れ、雨、曇りなど）
    api_source VARCHAR(50),    -- データ取得元API
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- インデックスの作成
CREATE INDEX idx_sensor_place_id ON sensor(place_id);
CREATE INDEX idx_prediction_model_sensor_id ON prediction_model(sensor_id);
CREATE INDEX idx_actual_score_measured_date_id ON actual_score(measured_date_id);
CREATE INDEX idx_predicted_score_model_id ON predicted_score(model_id);
CREATE INDEX idx_predicted_score_target_date_id ON predicted_score(target_date_id);
CREATE INDEX idx_actual_predictions_actual_score_id ON actual_predictions(actual_score_id);
CREATE INDEX idx_actual_predictions_predicted_score_id ON actual_predictions(predicted_score_id);
CREATE INDEX idx_actual_predictions_date_date ON actual_predictions_date(date);
CREATE INDEX idx_weather_data_date_id ON weather_data(date_id);