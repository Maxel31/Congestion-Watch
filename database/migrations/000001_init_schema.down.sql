-- マイグレーション: 初期スキーマ削除
-- 作成日: 2025-06-25
-- バージョン: 000001

-- テーブルを逆順で削除
DROP TABLE IF EXISTS predicted_score CASCADE;
DROP TABLE IF EXISTS actual_score CASCADE;
DROP TABLE IF EXISTS weather CASCADE;
DROP TABLE IF EXISTS prediction_model CASCADE;
DROP TABLE IF EXISTS sensor CASCADE;
DROP TABLE IF EXISTS place CASCADE;