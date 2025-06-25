-- 初期データ挿入スクリプト
-- 作成日: 2025-06-25

-- サンプル場所データ（静岡県浜松市中央区）
INSERT INTO place (name) VALUES 
    ('南館食堂'),
    ('北館食堂')
ON CONFLICT DO NOTHING;

-- サンプル日付データ
INSERT INTO actual_predictions_date (date) VALUES 
    ('2025-06-25'),
    ('2025-06-26'),
    ('2025-06-27')
ON CONFLICT (date) DO NOTHING;