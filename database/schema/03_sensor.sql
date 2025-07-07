-- センサーテーブル
CREATE TABLE IF NOT EXISTS sensor (
    id BIGSERIAL PRIMARY KEY,
    place_id BIGINT NOT NULL REFERENCES place(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_sensor_place_id ON sensor(place_id);