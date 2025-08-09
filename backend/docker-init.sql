-- PostgreSQL initialization script for Sonicus
-- This script sets up the database schema and initial configuration

-- Create the user if it doesn't exist (for PostgreSQL 15+)
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'sonicus_user') THEN

      CREATE ROLE sonicus_user LOGIN PASSWORD 'sonicus_pass';
   END IF;
END
$do$;

-- Create the database
CREATE DATABASE sonicus_dev WITH OWNER sonicus_user;

-- Connect to the new database
\c sonicus_dev

-- Create the sonicus schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS sonicus;

-- Set the default search path to use the sonicus schema
ALTER DATABASE sonicus_dev SET search_path TO sonicus, public;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Grant permissions to sonicus_user
GRANT ALL PRIVILEGES ON SCHEMA sonicus TO sonicus_user;
GRANT ALL PRIVILEGES ON DATABASE sonicus_dev TO sonicus_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA sonicus TO sonicus_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA sonicus TO sonicus_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA sonicus TO sonicus_user;

-- Set timezone
SET timezone = 'UTC';

-- Optional: Create some initial data or configuration
-- You can add initial data setup here if needed

COMMENT ON SCHEMA sonicus IS 'Sonicus application schema for therapy sounds and wellness platform';
