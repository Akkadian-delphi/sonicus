-- PostgreSQL initialization script for Sonicus
-- This script sets up the database schema and initial configuration

-- Create the sonicus schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS sonicus;

-- Set the default search path to use the sonicus schema
ALTER DATABASE sonicus_db SET search_path TO sonicus, public;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA sonicus TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA sonicus TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA sonicus TO postgres;

-- Set timezone
SET timezone = 'UTC';

-- Optional: Create some initial data or configuration
-- You can add initial data setup here if needed

COMMENT ON SCHEMA sonicus IS 'Sonicus application schema for therapy sounds and wellness platform';
