-- =============================================================================
-- Congestion Watch データベース初期化スクリプト
-- =============================================================================
-- このファイルはDocker Compose起動時に自動的に実行されます
-- 実行順序:
-- 1. データベース作成
-- 2. ユーザー作成と権限設定
-- 3. テーブル作成
-- 4. 初期データ投入
-- =============================================================================

-- データベース作成（既に存在する場合はスキップ）
SELECT 'CREATE DATABASE congestion_watch'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'congestion_watch')\gexec

-- 作成したDBに接続
\c congestion_watch;

-- =============================================================================
-- ユーザー作成と権限設定
-- =============================================================================

-- ユーザーが存在しない場合のみ作成
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_user
      WHERE  usename = 'congestion_user') THEN
      CREATE USER congestion_user WITH PASSWORD 'secure_password';
   END IF;
END
$do$;

-- 権限の付与
GRANT ALL PRIVILEGES ON DATABASE congestion_watch TO congestion_user;
GRANT ALL ON SCHEMA public TO congestion_user;

-- =============================================================================
-- テーブル作成
-- =============================================================================

-- 場所テーブル
CREATE TABLE IF NOT EXISTS place (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- センサーテーブル
CREATE TABLE IF NOT EXISTS sensor (
    id SERIAL PRIMARY KEY,
    place_id INTEGER NOT NULL REFERENCES place(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 予測モデルテーブル
CREATE TABLE IF NOT EXISTS prediction_model (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES sensor(id) ON DELETE CASCADE,
    model_params JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 実測スコアテーブル
CREATE TABLE IF NOT EXISTS actual_score (
    id SERIAL PRIMARY KEY,
    score INTEGER NOT NULL,
    place_id INTEGER NOT NULL REFERENCES place(id) ON DELETE CASCADE,
    target_datetime TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 予測スコアテーブル
CREATE TABLE IF NOT EXISTS predicted_score (
    id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES prediction_model(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    place_id INTEGER NOT NULL REFERENCES place(id) ON DELETE CASCADE,
    target_datetime TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 天候テーブル
CREATE TABLE IF NOT EXISTS weather (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP NOT NULL,
    weather VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- インデックスの作成
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_sensor_place_id ON sensor(place_id);
CREATE INDEX IF NOT EXISTS idx_prediction_model_sensor_id ON prediction_model(sensor_id);
CREATE INDEX IF NOT EXISTS idx_actual_score_place_id ON actual_score(place_id);
CREATE INDEX IF NOT EXISTS idx_actual_score_target_datetime ON actual_score(target_datetime);
CREATE INDEX IF NOT EXISTS idx_predicted_score_model_id ON predicted_score(model_id);
CREATE INDEX IF NOT EXISTS idx_predicted_score_place_id ON predicted_score(place_id);
CREATE INDEX IF NOT EXISTS idx_predicted_score_target_datetime ON predicted_score(target_datetime);
CREATE INDEX IF NOT EXISTS idx_weather_datetime ON weather(datetime);

-- =============================================================================
-- 権限の再設定（テーブル作成後）
-- =============================================================================

-- 全テーブルへの権限付与
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO congestion_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO congestion_user;

-- 将来作成されるオブジェクトへのデフォルト権限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO congestion_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO congestion_user;

-- =============================================================================
-- 初期データ投入（サンプルデータ）
-- =============================================================================

-- 場所データ（サンプル）
INSERT INTO place (name) VALUES 
    ('北館食堂（サンプル）')
ON CONFLICT DO NOTHING;

-- センサーデータ（サンプル）
INSERT INTO sensor (place_id) 
SELECT id FROM place 
ON CONFLICT DO NOTHING;

-- 予測モデルデータ（サンプル）
INSERT INTO prediction_model (sensor_id, model_params) 
SELECT 
    s.id,
    '{"algorithm": "linear_regression", "parameters": {"max_depth": 10}, "note": "sample_model"}'::jsonb
FROM sensor s
JOIN place p ON s.place_id = p.id
ON CONFLICT DO NOTHING;

-- 実測スコアデータ（サンプル）
INSERT INTO actual_score (score, place_id, target_datetime)
SELECT 
    CASE 
        -- 昼食時間帯（11-13時）に混雑
        WHEN EXTRACT(hour FROM dt) BETWEEN 11 AND 13 THEN 60 + (random() * 40)::int
        -- 夕食時間帯（17-19時）に混雑
        WHEN EXTRACT(hour FROM dt) BETWEEN 17 AND 19 THEN 50 + (random() * 30)::int
        -- その他の時間帯
        ELSE 10 + (random() * 20)::int
    END,
    p.id,
    dt
FROM place p
CROSS JOIN generate_series(
    CURRENT_DATE - INTERVAL '2 days',
    CURRENT_DATE - INTERVAL '1 hour',
    INTERVAL '30 minutes'
) AS dt
ON CONFLICT DO NOTHING;

-- 予測スコアデータ（実測データに基づく予測）
INSERT INTO predicted_score (model_id, score, place_id, target_datetime)
SELECT 
    pm.id,
    a.score + (-5 + (random() * 10)::int), -- 実測値に±5の誤差を付けた予測値
    a.place_id,
    a.target_datetime
FROM actual_score a
JOIN place p ON a.place_id = p.id
JOIN sensor s ON p.id = s.place_id
JOIN prediction_model pm ON s.id = pm.sensor_id
WHERE a.target_datetime >= CURRENT_DATE - INTERVAL '1 day'
ON CONFLICT DO NOTHING;

-- 未来の予測データ（今後24時間）- サンプル
INSERT INTO predicted_score (model_id, score, place_id, target_datetime)
SELECT 
    pm.id,
    CASE 
        -- 昼食時間帯の予測
        WHEN EXTRACT(hour FROM dt) BETWEEN 11 AND 13 THEN 55 + (random() * 20)::int
        -- 夕食時間帯の予測
        WHEN EXTRACT(hour FROM dt) BETWEEN 17 AND 19 THEN 45 + (random() * 15)::int
        -- その他の時間帯
        ELSE 8 + (random() * 12)::int
    END,
    p.id,
    dt
FROM place p
JOIN sensor s ON p.id = s.place_id
JOIN prediction_model pm ON s.id = pm.sensor_id
CROSS JOIN generate_series(
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '24 hours',
    INTERVAL '1 hour'
) AS dt
ON CONFLICT DO NOTHING;

-- 天気データ（サンプル - 過去3日分と今後の予報）
INSERT INTO weather (datetime, weather) 
SELECT 
    dt,
    CASE (random() * 4)::int
        WHEN 0 THEN '晴れ（サンプル）'
        WHEN 1 THEN '曇り（サンプル）'
        WHEN 2 THEN '雨（サンプル）'
        ELSE '晴れ時々曇り（サンプル）'
    END
FROM generate_series(
    CURRENT_DATE - INTERVAL '3 days',
    CURRENT_DATE + INTERVAL '2 days',
    INTERVAL '3 hours'
) AS dt
ON CONFLICT DO NOTHING;

-- =============================================================================
-- 初期化完了メッセージ
-- =============================================================================

DO $$
DECLARE
    place_count INTEGER;
    actual_score_count INTEGER;
    predicted_score_count INTEGER;
    weather_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO place_count FROM place;
    SELECT COUNT(*) INTO actual_score_count FROM actual_score;
    SELECT COUNT(*) INTO predicted_score_count FROM predicted_score;
    SELECT COUNT(*) INTO weather_count FROM weather;
    
    RAISE NOTICE '';
    RAISE NOTICE '=== Congestion Watch データベース初期化完了 ===';
    RAISE NOTICE '場所データ: % 件（北館食堂のみ）', place_count;
    RAISE NOTICE '実測スコアデータ: % 件', actual_score_count;
    RAISE NOTICE '予測スコアデータ: % 件', predicted_score_count;
    RAISE NOTICE '天気データ: % 件', weather_count;
    RAISE NOTICE '※ すべてサンプルデータです';
    RAISE NOTICE '==========================================';
END $$;