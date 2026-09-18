-- ============================================================
-- 05_create_agent.sql
-- Creates the Cortex Agent and Streamlit app
-- ============================================================

USE DATABASE INSURANCE_AI_HUB;
USE SCHEMA ANALYTICS;
USE WAREHOUSE AI_HUB_WH;

-- ============================================================
-- CORTEX AGENT
-- ============================================================
-- NOTE: Replace 'AI_HUB_WH' with your warehouse name if different.

CREATE OR REPLACE AGENT INSURANCE_AI_HUB.ANALYTICS.CLAIMS_FRAUD_TRIAGE_AGENT
  COMMENT = 'Claims Fraud Triage Copilot — combines structured data queries with policy document search to help adjusters assess claim risk.'
  PROFILE = '{"display_name": "Claims Fraud Triage Copilot", "color": "teal"}'
  FROM SPECIFICATION
  $$
  orchestration:
    tool_not_accessible: accept
    budget:
      seconds: 60
      tokens: 16000

  models:
    orchestration: auto

  instructions:
    response: >
      You are the Claims Fraud Triage Copilot for an insurance company. You help claims adjusters
      assess whether a claim is legitimate and flag suspicious ones. When asked about a specific claim:
      1. Use the Analyst tool to pull structured facts (claim details, policy info, customer history, fraud score).
      2. Use the PolicySearch tool to find relevant policy clauses, exclusions, or coverage terms.
      3. Synthesize both into a clear risk verdict: LOW RISK (fast-track), MEDIUM RISK (standard review), or HIGH RISK (escalate to investigation).
      Always cite specific data points and policy clauses in your assessment. Be concise and actionable.
    orchestration: >
      For questions about claim amounts, fraud scores, policy status, customer history, billing,
      agents, or any numeric/structured data, use the InsuranceAnalyst tool.
      For questions about policy documents, coverage clauses, exclusions, terms, or contract language, use the PolicySearch tool.
      For claim triage requests, use BOTH tools: first InsuranceAnalyst for structured facts, then PolicySearch for relevant clauses.
    sample_questions:
      - question: "Is claim CLM-00050 suspicious? Should I fast-track or investigate?"
      - question: "What are the top 10 highest fraud score claims currently open?"
      - question: "What exclusions apply to auto insurance policies?"
      - question: "Show me claims by type and their average fraud scores"

  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "InsuranceAnalyst"
        description: >
          Queries structured insurance data: claims (amounts, fraud scores, status, dates),
          policies (types, premiums, coverage, deductibles), customers (demographics, risk tier, credit score),
          billing (payments, outstanding balances), agents (performance, specialization),
          and at-risk policies (churn probability, risk scores). Use for any numeric,
          aggregate, or tabular question about insurance operations.
    - tool_spec:
        type: "cortex_search"
        name: "PolicySearch"
        description: >
          Searches insurance policy documents and contract text. Returns relevant clauses
          including coverage terms, exclusion clauses, benefits schedules, and policy conditions.
          Use when the question involves policy language, coverage details, exclusions, or
          contract-specific information. Input should be a natural language description of
          what policy information is needed.

  tool_resources:
    InsuranceAnalyst:
      semantic_view: "INSURANCE_AI_HUB.ANALYTICS.INSURANCE_SEMANTIC_MODEL"
      execution_environment:
        type: warehouse
        warehouse: "AI_HUB_WH"
    PolicySearch:
      search_service: "INSURANCE_AI_HUB.DOCUMENTS.POLICY_SEARCH_SVC"
      max_results: "5"
      title_column: "DOCUMENT_TITLE"
      columns_and_descriptions:
        CONTENT_TEXT:
          description: "The full text content of the policy document including coverage terms, exclusion clauses, and benefits schedules"
          type: "string"
          searchable: true
          filterable: false
        DOCUMENT_TYPE:
          description: "Type of document. Values include: Policy Contract, Endorsement, Rider, Amendment"
          type: "string"
          searchable: false
          filterable: true
        POLICY_ID:
          description: "The unique policy identifier this document belongs to, e.g. POL-00001"
          type: "string"
          searchable: false
          filterable: true
  $$;

-- ============================================================
-- STREAMLIT APP
-- ============================================================
-- First, upload streamlit_app.py to the stage:
--   PUT file://streamlit/streamlit_app.py @INSURANCE_AI_HUB.ANALYTICS.STREAMLIT_STAGE/
--       OVERWRITE=TRUE AUTO_COMPRESS=FALSE;

CREATE OR REPLACE STREAMLIT INSURANCE_AI_HUB.ANALYTICS.CLAIMS_FRAUD_TRIAGE_COPILOT
    ROOT_LOCATION = '@INSURANCE_AI_HUB.ANALYTICS.STREAMLIT_STAGE'
    MAIN_FILE = 'streamlit_app.py'
    QUERY_WAREHOUSE = 'AI_HUB_WH'
    TITLE = 'Claims Fraud Triage Copilot'
    COMMENT = 'Unified AI assistant for insurance claim fraud triage — combines Cortex Agent, dashboard analytics, and data quality monitoring';

-- ============================================================
-- VERIFICATION — test the agent
-- ============================================================
-- Uncomment and run to verify:
/*
SELECT TRY_PARSE_JSON(
    SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
        'INSURANCE_AI_HUB.ANALYTICS.CLAIMS_FRAUD_TRIAGE_AGENT',
        $${"messages": [{"role": "user", "content": [{"type": "text", "text": "Is claim CLM-00050 suspicious? Should I fast-track or investigate?"}]}]}$$
    )
) AS response;
*/
