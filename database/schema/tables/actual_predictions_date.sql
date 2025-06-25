-- 実測・予測日付テーブル
CREATE TABLE IF NOT EXISTS actual_predictions_date (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date)
);