-- ============================================================
-- 01_setup_database.sql
-- Creates the database, schemas, warehouse, and stage
-- ============================================================

USE ROLE SYSADMIN;

-- Create warehouse (skip if you already have one)
CREATE WAREHOUSE IF NOT EXISTS AI_HUB_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE;

-- Create database
CREATE DATABASE IF NOT EXISTS INSURANCE_AI_HUB;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS INSURANCE_AI_HUB.ANALYTICS;
CREATE SCHEMA IF NOT EXISTS INSURANCE_AI_HUB.DOCUMENTS;
CREATE SCHEMA IF NOT EXISTS INSURANCE_AI_HUB.DATA_QUALITY;

-- Create stage for Streamlit app
CREATE STAGE IF NOT EXISTS INSURANCE_AI_HUB.ANALYTICS.STREAMLIT_STAGE
    DIRECTORY = (ENABLE = TRUE);

-- Enable cross-region inference (recommended, run as ACCOUNTADMIN)
-- ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

-- Set default warehouse on your user (required for Cortex Agent)
-- ALTER USER <your_user> SET DEFAULT_WAREHOUSE = 'AI_HUB_WH';

USE WAREHOUSE AI_HUB_WH;
