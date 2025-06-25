-- 実測スコアテーブル
CREATE TABLE IF NOT EXISTS actual_score (
    id SERIAL PRIMARY KEY,
    score INTEGER NOT NULL,
    measured_date_id INTEGER NOT NULL REFERENCES actual_predictions_date(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);