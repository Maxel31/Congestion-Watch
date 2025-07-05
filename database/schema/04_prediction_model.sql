-- 予測モデルテーブル
CREATE TABLE IF NOT EXISTS prediction_model (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES sensor(id) ON DELETE CASCADE,
    model_params JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_prediction_model_sensor_id ON prediction_model(sensor_id);