-- 天候データテーブル
CREATE TABLE IF NOT EXISTS weather_data (
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