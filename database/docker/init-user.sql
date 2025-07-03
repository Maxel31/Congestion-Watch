-- ユーザー作成SQL
-- 作成日: 2025-07-03

-- congestion_userが存在しない場合のみ作成
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'congestion_user') THEN
        CREATE USER congestion_user WITH PASSWORD 'secure_password';
        GRANT ALL ON SCHEMA public TO congestion_user;
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO congestion_user;
        GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO congestion_user;
        
        -- 今後作成されるテーブルにも権限付与
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO congestion_user;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO congestion_user;
    END IF;
END
$$;

-- 現在のデータベースに対する権限を付与
GRANT ALL PRIVILEGES ON DATABASE congestion_watch_dev TO congestion_user;