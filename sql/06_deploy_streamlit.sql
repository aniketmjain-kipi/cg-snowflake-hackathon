-- =============================================================================
-- 06_deploy_streamlit.sql
-- Creates the stage and deploys the Streamlit app
-- IMPORTANT: Before running this, upload streamlit_app.py to the stage:
--   PUT 'file:///path/to/streamlit_app.py' @INSURANCE_AI_HUB.ANALYTICS.STREAMLIT_STAGE/
--       OVERWRITE=TRUE AUTO_COMPRESS=FALSE;
-- =============================================================================

USE DATABASE INSURANCE_AI_HUB;
USE SCHEMA ANALYTICS;
USE WAREHOUSE AI_HUB_WH;

-- Create stage for Streamlit app files
CREATE STAGE IF NOT EXISTS STREAMLIT_STAGE
    DIRECTORY = (ENABLE = TRUE);

-- Upload the app file (run from SnowSQL or Snowsight):
-- PUT 'file:///path/to/streamlit/streamlit_app.py' @STREAMLIT_STAGE/ OVERWRITE=TRUE AUTO_COMPRESS=FALSE;

-- Create the Streamlit app
CREATE OR REPLACE STREAMLIT CLAIMS_FRAUD_TRIAGE_COPILOT
    ROOT_LOCATION = '@INSURANCE_AI_HUB.ANALYTICS.STREAMLIT_STAGE'
    MAIN_FILE = 'streamlit_app.py'
    QUERY_WAREHOUSE = 'AI_HUB_WH'
    TITLE = 'Claims Fraud Triage Copilot'
    COMMENT = 'Unified AI assistant for insurance claim fraud triage — combines Cortex Agent, dashboard analytics, and data quality monitoring';
