-- 実測・予測関連テーブル
CREATE TABLE IF NOT EXISTS actual_predictions (
    id SERIAL PRIMARY KEY,
    actual_score_id INTEGER NOT NULL REFERENCES actual_score(id) ON DELETE CASCADE,
    predicted_score_id INTEGER NOT NULL REFERENCES predicted_score(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(actual_score_id, predicted_score_id)
);