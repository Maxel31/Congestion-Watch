-- 初期データ挿入スクリプト
-- 作成日: 2025-07-02
-- 更新: スプレッドシートからのデータ取得に対応、TIMESTAMP形式に変更

-- Sample location data
INSERT INTO place (name) VALUES 
    ('North Hall'),
    ('South Hall'),
    ('for debug')
ON CONFLICT DO NOTHING;

-- Sample sensor data
INSERT INTO sensor (place_id) VALUES 
    (1),  -- North Hall
    (2),  -- South Hall
    (3)   -- for debug
ON CONFLICT DO NOTHING;

-- Sample prediction model data
INSERT INTO prediction_model (sensor_id, model_params) VALUES 
    (1, '{"algorithm": "linear_regression", "parameters": {"max_depth": 10}}'),
    (2, '{"algorithm": "random_forest", "parameters": {"n_estimators": 100}}'),
    (3, '{"algorithm": "neural_network", "parameters": {"hidden_layers": [64, 32]}}')
ON CONFLICT DO NOTHING;

-- Sample actual score data (with precise timestamps)
INSERT INTO actual_score (score, place_id, target_datetime) VALUES 
    (47, 1, '2025-07-02 13:43:03'),  -- North Hall: from spreadsheet sample
    (52, 1, '2025-07-02 14:15:22'),  -- North Hall: sample data
    (38, 1, '2025-07-02 15:30:45'),  -- North Hall: sample data
    (65, 2, '2025-07-02 13:45:00'),  -- South Hall: sample data
    (70, 2, '2025-07-02 14:20:15'),  -- South Hall: sample data
    (42, 3, '2025-07-02 16:00:00')   -- for debug: sample data
ON CONFLICT DO NOTHING;

-- Sample predicted score data (with precise timestamps)
INSERT INTO predicted_score (model_id, score, place_id, target_datetime) VALUES 
    (1, 45, 1, '2025-07-02 13:43:03'),  -- North Hall: prediction vs actual 47
    (1, 50, 1, '2025-07-02 14:15:22'),  -- North Hall: prediction vs actual 52
    (2, 62, 2, '2025-07-02 13:45:00'),  -- South Hall: prediction vs actual 65
    (2, 68, 2, '2025-07-02 14:20:15'),  -- South Hall: prediction vs actual 70
    (3, 40, 3, '2025-07-02 16:00:00'),  -- for debug: prediction vs actual 42
    (1, 48, 1, '2025-07-02 17:00:00'),  -- North Hall: future prediction
    (2, 72, 2, '2025-07-02 17:00:00')   -- South Hall: future prediction
ON CONFLICT DO NOTHING;

-- Sample weather data (with precise timestamps)
INSERT INTO weather (datetime, weather) VALUES 
    ('2025-07-02 13:00:00', 'cloudy'),
    ('2025-07-02 14:00:00', 'partly_cloudy'),
    ('2025-07-02 15:00:00', 'sunny'),
    ('2025-07-02 16:00:00', 'sunny'),
    ('2025-07-02 17:00:00', 'cloudy')
ON CONFLICT DO NOTHING;