-- This script creates two database users:
-- 1. milestone_admin (full access)
-- 2. milestone_readonly (read-only access)

-- Create read-only user
CREATE USER milestone_readonly WITH PASSWORD 'your_readonly_password_here';

-- Grant connect privilege
GRANT CONNECT ON DATABASE milestone_db TO milestone_readonly;

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO milestone_readonly;

-- Grant select on all existing tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO milestone_readonly;

-- Grant select on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO milestone_readonly;

-- Grant select on all sequences (for id columns)
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO milestone_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO milestone_readonly;
