-- =============================================================================
-- table/view 初期化スクリプト
-- =============================================================================

-- 特定の日にちにおける最新のactual_score.scoreと最新の日時以降のpredicted_score.scoreを取得するビュー
    
DROP VIEW IF EXISTS cloud_data;
CREATE VIEW cloud_data AS
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
LEFT JOIN actual_score acs
  ON ps.place_id = acs.place_id 
  AND ps.target_datetime = acs.target_datetime;