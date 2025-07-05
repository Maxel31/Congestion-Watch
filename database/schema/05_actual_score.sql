-- 実測スコアテーブル
CREATE TABLE IF NOT EXISTS actual_score (
    id SERIAL PRIMARY KEY,
    score INTEGER NOT NULL,
    place_id INTEGER NOT NULL REFERENCES place(id) ON DELETE CASCADE,
    target_datetime TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_actual_score_place_id ON actual_score(place_id);
CREATE INDEX IF NOT EXISTS idx_actual_score_target_datetime ON actual_score(target_datetime);
CREATE INDEX IF NOT EXISTS idx_actual_score_join ON actual_score(place_id, target_datetime) INCLUDE (score);