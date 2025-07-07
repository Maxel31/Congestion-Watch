-- 天候テーブル
CREATE TABLE IF NOT EXISTS weather (
    id BIGSERIAL PRIMARY KEY,
    datetime TIMESTAMP NOT NULL,
    weather VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_weather_datetime ON weather(datetime);