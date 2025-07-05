-- =============================================================================
-- Sample Data Seed Script
-- =============================================================================

-- 場所データ
INSERT INTO place (name) VALUES 
('南館食堂'),
('北館食堂')
ON CONFLICT DO NOTHING;

-- 天気データ
INSERT INTO weather (datetime, weather) VALUES
('2025-07-05 12:00:00', '晴れ'),
('2025-07-05 18:00:00', '曇り'),
('2025-07-06 12:00:00', '雨'),
('2025-07-06 18:00:00', '晴れ'),
('2025-07-07 12:00:00', '曇り')
ON CONFLICT DO NOTHING;

-- センサーデータ
INSERT INTO sensor (place_id) VALUES
(1), -- 南館食堂
(2)  -- 北館食堂
ON CONFLICT DO NOTHING;

-- 予測モデルデータ
INSERT INTO prediction_model (sensor_id, model_params) VALUES
(1, '{"algorithm": "linear_regression", "features": ["time", "weather"], "accuracy": 0.85}'),
(2, '{"algorithm": "random_forest", "features": ["time", "weather", "day_of_week"], "accuracy": 0.88}'),
(1, '{"algorithm": "neural_network", "features": ["time", "weather", "season"], "accuracy": 0.92}'),
(2, '{"algorithm": "svm", "features": ["time", "weather"], "accuracy": 0.78}'),
(1, '{"algorithm": "xgboost", "features": ["time", "weather", "day_of_week"], "accuracy": 0.90}')
ON CONFLICT DO NOTHING;

-- 実測スコアデータ（過去データ）
INSERT INTO actual_score (score, place_id, target_datetime) VALUES
-- 2025-07-05 data
(85, 1, '2025-07-05 12:00:00'), -- 南館食堂 lunch time
(45, 1, '2025-07-05 15:00:00'), -- 南館食堂 afternoon
(75, 1, '2025-07-05 18:00:00'), -- 南館食堂 dinner time

(90, 2, '2025-07-05 12:00:00'), -- 北館食堂 lunch time
(30, 2, '2025-07-05 15:00:00'), -- 北館食堂 afternoon
(80, 2, '2025-07-05 18:00:00'), -- 北館食堂 dinner time

-- 2025-07-06 data (partial)
(88, 1, '2025-07-06 12:00:00'), -- 南館食堂 lunch time
(95, 2, '2025-07-06 12:00:00'), -- 北館食堂 lunch time
(40, 1, '2025-07-06 15:00:00'), -- 南館食堂 afternoon
(35, 2, '2025-07-06 15:00:00'), -- 北館食堂 afternoon
(70, 1, '2025-07-06 18:00:00'), -- 南館食堂 dinner time
(75, 2, '2025-07-06 18:00:00')  -- 北館食堂 dinner time
ON CONFLICT DO NOTHING;

-- 予測スコアデータ（過去・現在・未来データ）
INSERT INTO predicted_score (model_id, score, place_id, target_datetime) VALUES
-- 2025-07-05 prediction data (for comparison with actual values)
(1, 82, 1, '2025-07-05 12:00:00'), -- 南館食堂 lunch (compare with actual 85)
(1, 47, 1, '2025-07-05 15:00:00'), -- 南館食堂 afternoon (compare with actual 45)
(1, 73, 1, '2025-07-05 18:00:00'), -- 南館食堂 dinner (compare with actual 75)

(2, 88, 2, '2025-07-05 12:00:00'), -- 北館食堂 lunch (compare with actual 90)
(2, 32, 2, '2025-07-05 15:00:00'), -- 北館食堂 afternoon (compare with actual 30)
(2, 78, 2, '2025-07-05 18:00:00'), -- 北館食堂 dinner (compare with actual 80)

-- 2025-07-06 prediction data (some actual values available)
(1, 86, 1, '2025-07-06 12:00:00'), -- 南館食堂 lunch (compare with actual 88)
(1, 42, 1, '2025-07-06 15:00:00'), -- 南館食堂 afternoon (compare with actual 40)
(1, 68, 1, '2025-07-06 18:00:00'), -- 南館食堂 dinner (compare with actual 70)

(2, 92, 2, '2025-07-06 12:00:00'), -- 北館食堂 lunch (compare with actual 95)
(2, 37, 2, '2025-07-06 15:00:00'), -- 北館食堂 afternoon (compare with actual 35)
(2, 77, 2, '2025-07-06 18:00:00'), -- 北館食堂 dinner (compare with actual 75)

-- 2025-07-07 prediction data (future data, no actual values)
(1, 80, 1, '2025-07-07 12:00:00'), -- 南館食堂 lunch
(1, 45, 1, '2025-07-07 15:00:00'), -- 南館食堂 afternoon
(1, 70, 1, '2025-07-07 18:00:00'), -- 南館食堂 dinner

(2, 85, 2, '2025-07-07 12:00:00'), -- 北館食堂 lunch
(2, 40, 2, '2025-07-07 15:00:00'), -- 北館食堂 afternoon
(2, 75, 2, '2025-07-07 18:00:00'), -- 北館食堂 dinner

-- 複数バージョンの予測データ（最新版選択テスト用）
-- 古いバージョン（created_atが古い）
(1, 75, 1, '2025-07-05 12:00:00'), -- 南館食堂 old prediction (82 should be selected as latest)
(2, 85, 2, '2025-07-05 12:00:00')  -- 北館食堂 old prediction (88 should be selected as latest)
ON CONFLICT DO NOTHING;

-- 古いバージョンの予測データのcreated_atを過去に設定
UPDATE predicted_score 
SET created_at = '2025-07-04 10:00:00' 
WHERE (model_id = 1 AND score = 75 AND place_id = 1 AND target_datetime = '2025-07-05 12:00:00')
   OR (model_id = 2 AND score = 85 AND place_id = 2 AND target_datetime = '2025-07-05 12:00:00');

-- データ投入完了メッセージ
DO $$
BEGIN
    RAISE NOTICE 'サンプルデータの投入が完了しました';
    RAISE NOTICE '場所: % 件', (SELECT COUNT(*) FROM place);
    RAISE NOTICE '天気: % 件', (SELECT COUNT(*) FROM weather);
    RAISE NOTICE 'センサー: % 件', (SELECT COUNT(*) FROM sensor);
    RAISE NOTICE '予測モデル: % 件', (SELECT COUNT(*) FROM prediction_model);
    RAISE NOTICE '実測スコア: % 件', (SELECT COUNT(*) FROM actual_score);
    RAISE NOTICE '予測スコア: % 件', (SELECT COUNT(*) FROM predicted_score);
    RAISE NOTICE 'cloud_dataビューのテストデータが準備されました';
END $$;
