-- 予測スコアテーブル
CREATE TABLE IF NOT EXISTS predicted_score (
    id BIGSERIAL PRIMARY KEY,
    model_id BIGINT NOT NULL REFERENCES prediction_model(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    place_id BIGINT NOT NULL REFERENCES place(id) ON DELETE CASCADE,
    target_datetime TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_predicted_score_model_id ON predicted_score(model_id);
CREATE INDEX IF NOT EXISTS idx_predicted_score_place_id ON predicted_score(place_id);
CREATE INDEX IF NOT EXISTS idx_predicted_score_target_datetime ON predicted_score(target_datetime);
CREATE INDEX IF NOT EXISTS idx_predicted_score_latest ON predicted_score(place_id, target_datetime, created_at DESC) INCLUDE (score);