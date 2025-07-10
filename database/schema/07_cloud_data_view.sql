-- =============================================================================
-- table/view 初期化スクリプト
-- =============================================================================

-- 特定の日にちにおける最新のactual_score.scoreと最新の日時以降のpredicted_score.scoreを取得するビュー
    
DROP VIEW IF EXISTS cloud_data;
CREATE VIEW cloud_data AS
-- predicted_scoreがあってactual_scoreもある場合
SELECT 
  ps.score as predicted_score,
  acs.score as actual_score,
  ps.target_datetime,
  ps.place_id
FROM (
  SELECT DISTINCT ON (place_id, target_datetime)
    place_id,
    target_datetime,
    score
  FROM predicted_score
  ORDER BY place_id, target_datetime, created_at DESC
) ps
LEFT JOIN (
  SELECT DISTINCT ON (place_id, target_datetime)
    place_id,
    target_datetime,
    score
  FROM actual_score
  ORDER BY place_id, target_datetime, created_at DESC
) acs
  ON ps.place_id = acs.place_id 
  AND ps.target_datetime = acs.target_datetime

UNION

-- actual_scoreがあってpredicted_scoreがない場合
SELECT 
  NULL as predicted_score,
  acs.score as actual_score,
  acs.target_datetime,
  acs.place_id
FROM (
  SELECT DISTINCT ON (place_id, target_datetime)
    place_id,
    target_datetime,
    score
  FROM actual_score
  ORDER BY place_id, target_datetime, created_at DESC
) acs
WHERE NOT EXISTS (
  SELECT 1 FROM predicted_score ps 
  WHERE ps.place_id = acs.place_id 
  AND ps.target_datetime = acs.target_datetime
);
