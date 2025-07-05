-- センサーテーブル
CREATE TABLE IF NOT EXISTS sensor (
    id SERIAL PRIMARY KEY,
    place_id INTEGER NOT NULL REFERENCES place(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_sensor_place_id ON sensor(place_id);