# Claims Fraud Triage Copilot

> One AI assistant that reads claims, policies, and documents together — so adjusters fast-track honest claims and focus on the ones that actually need a human.

Built on **Snowflake Cortex Agent** | **Cortex Analyst** | **Cortex Search** | **Streamlit in Snowflake**

---

## Architecture

```
User Question
     |
     v
+-----------------------------+
|   Streamlit App (Chat Tab)  |
|   DATA_AGENT_RUN() call     |
+--------------+--------------+
               |
               v
+-----------------------------+
|   Cortex Agent              |
|   (CLAIMS_FRAUD_TRIAGE)     |
|   Routes to tools based     |
|   on question intent        |
+------+--------------+-------+
       |              |
       v              v
+--------------+ +--------------+
| Cortex       | | Cortex       |
| Analyst      | | Search       |
| (Structured) | | (Documents)  |
|              | |              |
| Claims,      | | Policy text, |
| Policies,    | | Exclusions,  |
| Customers,   | | Coverage     |
| Billing      | | clauses      |
+------+-------+ +------+-------+
       |                |
       v                v
+-----------------------------+
|  Agent synthesizes both     |
|  into a risk verdict:       |
|  LOW / MEDIUM / HIGH RISK   |
|  with cited evidence        |
+-----------------------------+
```

## Project Structure

```
.
├── README.md                          # This file
├── docs/
│   └── prompt_playbook.md             # 3-prompt guide to recreate from scratch
├── sql/
│   ├── 01_setup_database.sql          # Database, schemas, warehouse
│   ├── 02_create_tables.sql           # All 12 table DDLs
│   ├── 03_create_semantic_view.sql    # Semantic view for Cortex Analyst
│   ├── 04_create_search_service.sql   # Cortex Search on policy docs
│   └── 05_create_agent.sql            # Cortex Agent with both tools
├── streamlit/
│   └── streamlit_app.py               # 3-tab Streamlit app
└── assets/
    └── flatten_Claims_Fraud_Triage_Copilot.pdf  # Design document (optional)
```

## Quick Start

### Prerequisites

- Snowflake account with **ACCOUNTADMIN** or **SYSADMIN** role
- A warehouse (X-Small is sufficient)
- Cross-region inference enabled (recommended):
  ```sql
  ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';
  ```
- Default warehouse set on your user:
  ```sql
  ALTER USER <your_user> SET DEFAULT_WAREHOUSE = '<your_warehouse>';
  ```

### Deploy (run SQL scripts in order)

```bash
# 1. Create database, schemas, warehouse
#    Run: sql/01_setup_database.sql

# 2. Create tables and load mock data
#    Run: sql/02_create_tables.sql

# 3. Create semantic view
#    Run: sql/03_create_semantic_view.sql

# 4. Create Cortex Search service
#    Run: sql/04_create_search_service.sql

# 5. Create Cortex Agent
#    Run: sql/05_create_agent.sql
```

Then deploy the Streamlit app:
```sql
-- Upload streamlit_app.py to the stage
PUT file://streamlit/streamlit_app.py @INSURANCE_AI_HUB.ANALYTICS.STREAMLIT_STAGE/
  OVERWRITE=TRUE AUTO_COMPRESS=FALSE;

-- Create the Streamlit app (already in 05_create_agent.sql)
```

### Verify

```sql
SELECT TRY_PARSE_JSON(
    SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
        'INSURANCE_AI_HUB.ANALYTICS.CLAIMS_FRAUD_TRIAGE_AGENT',
        $${"messages": [{"role": "user", "content": [{"type": "text", "text": "Is claim CLM-00050 suspicious? Should I fast-track or investigate?"}]}]}$$
    )
) AS response;
```

## Snowflake Objects Created

| Object | Type | Location |
|--------|------|----------|
| INSURANCE_AI_HUB | Database | -- |
| ANALYTICS | Schema | INSURANCE_AI_HUB |
| DOCUMENTS | Schema | INSURANCE_AI_HUB |
| DATA_QUALITY | Schema | INSURANCE_AI_HUB |
| CUSTOMERS (200 rows) | Table | ANALYTICS |
| POLICIES (300 rows) | Table | ANALYTICS |
| CLAIMS (400 rows) | Table | ANALYTICS |
| AGENTS (20 rows) | Table | ANALYTICS |
| BILLING (500 rows) | Table | ANALYTICS |
| AT_RISK_POLICIES (165 rows) | Table | ANALYTICS |
| POLICY_DOCUMENTS (10 rows) | Table | DOCUMENTS |
| DOCUMENT_CHUNKS (25 rows) | Table | DOCUMENTS |
| DQ_RULES (50 rows) | Table | DATA_QUALITY |
| DQ_RESULTS (40 rows) | Table | DATA_QUALITY |
| DQ_SCORES (28 rows) | Table | DATA_QUALITY |
| DQ_COLUMN_HEALTH (28 rows) | Table | DATA_QUALITY |
| INSURANCE_SEMANTIC_MODEL | Semantic View | ANALYTICS |
| POLICY_SEARCH_SVC | Cortex Search Service | DOCUMENTS |
| CLAIMS_FRAUD_TRIAGE_AGENT | Cortex Agent | ANALYTICS |
| CLAIMS_FRAUD_TRIAGE_COPILOT | Streamlit App | ANALYTICS |

## Streamlit App Tabs

| Tab | Description | Powered By |
|-----|-------------|-----------|
| **Fraud Triage Chat** | Ask about any claim; get a risk verdict with evidence | Cortex Agent |
| **Claims Dashboard** | KPIs, charts, high-risk claims table | Direct SQL |
| **Data Quality** | DQ scores, trends, rule results, column health | Direct SQL |

## Tech Stack

- **Snowflake Cortex Agent** — orchestrates structured + unstructured tools
- **Cortex Analyst** — natural language to SQL via semantic view
- **Cortex Search** — semantic search over policy documents
- **Streamlit in Snowflake** — warehouse-runtime UI
- **AI_PARSE_DOCUMENT** — PDF extraction (used to analyze design doc)

## License

MIT
