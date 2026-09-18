-- ============================================================
-- 04_create_search_service.sql
-- Creates the Cortex Search service for policy documents
-- ============================================================

USE DATABASE INSURANCE_AI_HUB;
USE SCHEMA DOCUMENTS;
USE WAREHOUSE AI_HUB_WH;

-- Enable change tracking on source table (required for incremental refresh)
ALTER TABLE POLICY_DOCUMENTS SET CHANGE_TRACKING = TRUE;

-- Create the Cortex Search service
CREATE OR REPLACE CORTEX SEARCH SERVICE POLICY_SEARCH_SVC
    ON CONTENT_TEXT
    ATTRIBUTES POLICY_ID, DOCUMENT_TYPE, DOCUMENT_TITLE
    WAREHOUSE = 'AI_HUB_WH'
    TARGET_LAG = '1 minute'
    REFRESH_MODE = INCREMENTAL
    AS (
        SELECT
            DOCUMENT_ID,
            POLICY_ID,
            DOCUMENT_TYPE,
            DOCUMENT_TITLE,
            CONCAT_WS(' ',
                COALESCE(CONTENT_TEXT, ''),
                COALESCE(EXCLUSION_CLAUSES, ''),
                COALESCE(COVERAGE_SUMMARY, '')
            ) AS CONTENT_TEXT
        FROM INSURANCE_AI_HUB.DOCUMENTS.POLICY_DOCUMENTS
        WHERE DOCUMENT_STATUS = 'Active'
    );
