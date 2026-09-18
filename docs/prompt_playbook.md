# Claims Fraud Triage Copilot — Prompt Playbook
## A step-by-step guide to recreate the full solution from scratch

---

## What This Builds

A unified AI-powered insurance claims fraud triage system on Snowflake, consisting of:
- **12 tables** with mock data across 3 schemas (ANALYTICS, DOCUMENTS, DATA_QUALITY)
- **1 Semantic View** (Cortex Analyst) for structured data queries
- **1 Cortex Search Service** for policy document retrieval
- **1 Cortex Agent** that orchestrates both tools
- **1 Streamlit App** with 3 tabs: Chat, Dashboard, Data Quality

---

## Prerequisites

Before starting, ensure you have:
- A Snowflake account with **ACCOUNTADMIN** or **SYSADMIN** role
- A warehouse (e.g., `AI_HUB_WH`) — X-Small is sufficient
- Cross-region inference enabled (recommended):
  ```sql
  ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';
  ```
- Your user has a **default warehouse** and **default role** set:
  ```sql
  ALTER USER <your_user> SET DEFAULT_WAREHOUSE = '<your_warehouse>';
  ALTER USER <your_user> SET DEFAULT_ROLE = 'ACCOUNTADMIN';
  ```

---

## PROMPT 1: Analyze the PDF (optional — understand the design)

> **What to do:** Upload the hackathon PDF to a Snowflake stage, then ask CoCo to analyze it.

```
Analyze the pdf. '@"INSURANCE_AI_HUB"."DOCUMENTS"."TESTSTAGE"/flatten_Claims_Fraud_Triage_Copilot.pdf'
```

**What this does:** Extracts and summarizes the PDF architecture document using `AI_PARSE_DOCUMENT`. This gives CoCo the full context of what to build — the 3-schema design, entity relationships, worked examples, and the end-to-end architecture.

**Tip:** If you don't have a PDF, skip this step and use Prompt 2 directly — it contains everything needed.

---

## PROMPT 2: Create the entire end-to-end solution

> **This is the main prompt. It creates everything in one shot.**

```
Create an end-to-end Claims Fraud Triage Copilot solution for an insurance company on Snowflake.

## Database & Schema Setup
Create database INSURANCE_AI_HUB with 3 schemas:
- ANALYTICS — structured operational data
- DOCUMENTS — policy documents and embeddings
- DATA_QUALITY — trust scoring and monitoring

## Tables & Mock Data (create all tables WITH realistic mock data):

### ANALYTICS schema:
1. CUSTOMERS (200 rows) — CUSTOMER_ID, FIRST_NAME, LAST_NAME, DATE_OF_BIRTH, GENDER, EMAIL, PHONE, ADDRESS, CITY, STATE, ZIP_CODE, RISK_TIER (Low/Medium/High), CREDIT_SCORE, CUSTOMER_SINCE, SEGMENT (Individual/Family/Corporate)
2. POLICIES (300 rows) — POLICY_ID, CUSTOMER_ID, AGENT_ID, POLICY_TYPE (Health/Auto/Life/Home), POLICY_STATUS, START_DATE, END_DATE, PREMIUM_AMOUNT, COVERAGE_AMOUNT, DEDUCTIBLE, LOSS_RATIO, PLAN_TIER (Bronze/Silver/Gold/Platinum), PAYMENT_FREQUENCY, AUTO_RENEW
3. CLAIMS (400 rows) — CLAIM_ID, POLICY_ID, CUSTOMER_ID, CLAIM_DATE, CLAIM_TYPE, CLAIM_STATUS (Open/Approved/Denied/Under Investigation), CLAIM_AMOUNT, APPROVED_AMOUNT, FRAUD_FLAG, FRAUD_SCORE (0-1), ASSIGNED_ADJUSTER, RESOLUTION_DATE, DAYS_TO_RESOLVE, FRICTION_POINT, PRIORITY
4. AGENTS (20 rows) — AGENT_ID, AGENT_NAME, AGENT_TYPE, REGION, BRANCH, HIRE_DATE, LICENSE_NUMBER, SPECIALIZATION, PERFORMANCE_RATING, ACTIVE_FLAG
5. BILLING (500 rows) — BILLING_ID, POLICY_ID, CUSTOMER_ID, INVOICE_DATE, DUE_DATE, AMOUNT_DUE, AMOUNT_PAID, OUTSTANDING_BALANCE, PAYMENT_STATUS, PAYMENT_METHOD, PAYMENT_DATE, LATE_FEE
6. AT_RISK_POLICIES (165 rows) — RISK_ID, POLICY_ID, CUSTOMER_ID, RISK_CATEGORY, RISK_SCORE, REVENUE_AT_RISK, CHURN_PROBABILITY, LAST_INTERACTION_DATE, DAYS_SINCE_CONTACT, COMPLAINTS_COUNT, MISSED_PAYMENTS, RECOMMENDED_ACTION, IDENTIFIED_DATE

### DOCUMENTS schema:
7. POLICY_DOCUMENTS (10 rows) — DOCUMENT_ID, POLICY_ID, DOCUMENT_TYPE, DOCUMENT_TITLE, FILE_NAME, FILE_FORMAT, UPLOAD_DATE, CONTENT_TEXT, EXCLUSION_CLAUSES, COVERAGE_SUMMARY, PAGE_COUNT, DOCUMENT_STATUS
8. DOCUMENT_CHUNKS (25 rows) — CHUNK_ID, DOCUMENT_ID, CHUNK_INDEX, CHUNK_TEXT, SECTION_TITLE, TOKEN_COUNT, EMBEDDING

### DATA_QUALITY schema:
9. DQ_RULES (50 rows) — RULE_ID, RULE_NAME, RULE_DESCRIPTION, TARGET_TABLE, TARGET_COLUMN, RULE_TYPE (Completeness/Validity/Consistency/Timeliness), RULE_EXPRESSION, SEVERITY, IS_CRITICAL, THRESHOLD_PCT, ACTIVE_FLAG
10. DQ_RESULTS (40 rows) — RESULT_ID, RULE_ID, EXECUTION_DATE, TARGET_TABLE, TARGET_COLUMN, TOTAL_RECORDS, PASSED_RECORDS, FAILED_RECORDS, PASS_RATE, STATUS, ERROR_SAMPLE
11. DQ_SCORES (28 rows) — SCORE_ID, TABLE_NAME, SCHEMA_NAME, SCORE_DATE, OVERALL_SCORE, COMPLETENESS_SCORE, ACCURACY_SCORE, CONSISTENCY_SCORE, TIMELINESS_SCORE, RULES_PASSED, RULES_FAILED, TOTAL_RULES, TREND (UP/DOWN/FLAT)
12. DQ_COLUMN_HEALTH (28 rows) — HEALTH_ID, TABLE_NAME, COLUMN_NAME, CHECK_DATE, NULL_PCT, DISTINCT_COUNT, DUPLICATE_PCT, OUTLIER_COUNT, FORMAT_VIOLATION_COUNT, HEALTH_STATUS (Healthy/Warning/Critical), SCORE, IS_CRITICAL

## Semantic View
Create a semantic view INSURANCE_AI_HUB.ANALYTICS.INSURANCE_SEMANTIC_MODEL covering CUSTOMERS, POLICIES, CLAIMS, AGENTS, BILLING, AT_RISK_POLICIES with:
- All relationships defined (Claims→Policies, Claims→Customers, Policies→Agents, Policies→Customers, Billing→Policies, AtRisk→Policies)
- Metrics: TOTAL_PREMIUM, ACTIVE_POLICY_COUNT, AVG_LOSS_RATIO, AVG_FRAUD_SCORE, FRAUD_FLAGGED_COUNT, TOTAL_CLAIMS_PAID, AVG_RESOLUTION_DAYS, TOTAL_OUTSTANDING, TOTAL_REVENUE_AT_RISK
- Synonyms for business terms

## Cortex Search Service
Create INSURANCE_AI_HUB.DOCUMENTS.POLICY_SEARCH_SVC on POLICY_DOCUMENTS:
- Search column: concatenation of CONTENT_TEXT, EXCLUSION_CLAUSES, COVERAGE_SUMMARY
- Attribute columns: POLICY_ID, DOCUMENT_TYPE, DOCUMENT_TITLE
- Embedding model: snowflake-arctic-embed-m-v1.5
- Target lag: 1 minute

## Cortex Agent
Create INSURANCE_AI_HUB.ANALYTICS.CLAIMS_FRAUD_TRIAGE_AGENT with:
- Tool 1: "InsuranceAnalyst" (cortex_analyst_text_to_sql) → semantic view
- Tool 2: "PolicySearch" (cortex_search) → search service
- execution_environment with warehouse specified for the Analyst tool
- Instructions: triage claims using BOTH tools, produce LOW/MEDIUM/HIGH risk verdicts
- Sample questions about claim investigation, fraud scores, policy exclusions

## Streamlit App (IMPORTANT — warehouse-runtime compatible)
Create INSURANCE_AI_HUB.ANALYTICS.CLAIMS_FRAUD_TRIAGE_COPILOT with 3 tabs:

CRITICAL CONSTRAINTS for warehouse-runtime Streamlit:
- Do NOT use: st.chat_input, st.chat_message, hide_index=True, st.divider(), type="primary" on buttons, color= param in st.bar_chart, style.map(), st.experimental_rerun()
- DO use: st.form() with st.form_submit_button() for the chat input
- DO use: st.bar_chart() with .set_index() pattern for charts
- DO use: st.markdown("---") instead of st.divider()
- Use SNOWFLAKE.CORTEX.DATA_AGENT_RUN() (not SNOWFLAKE.CORTEX.AGENT) to call the agent
- Format large numbers as $X.XXM or $X.XK to avoid truncation in metric cards

Tab 1 — Fraud Triage Chat:
- st.form with text_input + form_submit_button (ensures Enter key works)
- Calls DATA_AGENT_RUN with the agent
- Parses response JSON: iterate content[] array, extract type="text" items
- Displays conversation history from session_state
- Sidebar with sample questions

Tab 2 — Claims Dashboard:
- KPI row: Total Claims, Open Claims, Avg Fraud Score, Total Payouts (formatted as $XM), Fraud Flagged, Avg Resolution Days
- Charts: Claims by Type, Claims by Status, Fraud Score Distribution, Top Friction Points
- Table: High-Risk Claims (fraud_score >= 0.7) with customer details

Tab 3 — Data Quality:
- Latest DQ scores per table with color-coded cards
- DQ score trend line chart over time
- Rule results summary table
- Column health table
```

---

## PROMPT 3: Test the agent (verify everything works)

```
Test the Cortex Agent by running this SQL:

SELECT TRY_PARSE_JSON(
    SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
        'INSURANCE_AI_HUB.ANALYTICS.CLAIMS_FRAUD_TRIAGE_AGENT',
        $${"messages": [{"role": "user", "content": [{"type": "text", "text": "Is claim CLM-00050 suspicious? Should I fast-track or investigate?"}]}]}$$
    )
) AS response;

Verify that:
1. The InsuranceAnalyst tool pulled structured claim/policy/customer data
2. The PolicySearch tool retrieved relevant policy clauses
3. The agent produced a risk verdict (LOW/MEDIUM/HIGH)
```

---

## Common Pitfalls & Fixes

### Pitfall 1: "Agent missing execution environment"
**Cause:** Cortex Analyst tool needs a warehouse.
**Fix:** Use `execution_environment` block in YAML:
```yaml
tool_resources:
  InsuranceAnalyst:
    semantic_view: "DB.SCHEMA.VIEW"
    execution_environment:
      type: warehouse
      warehouse: "MY_WH"
```
Also ensure the calling user has a default warehouse set:
```sql
ALTER USER <user> SET DEFAULT_WAREHOUSE = '<warehouse>';
```

### Pitfall 2: "st.chat_input not found" or "hide_index unexpected keyword"
**Cause:** Warehouse-runtime Streamlit uses an older version (~1.22).
**Fix:** Avoid all newer Streamlit APIs. See the constraints list in Prompt 2.

### Pitfall 3: "Ask button does nothing"
**Cause:** `st.text_input` + `st.button` have a widget timing issue in older Streamlit.
**Fix:** Wrap in `st.form()` with `st.form_submit_button()`. This ensures both Enter and click submit the value atomically.

### Pitfall 4: "SNOWFLAKE.CORTEX.AGENT unknown function"
**Cause:** The SQL function is `DATA_AGENT_RUN`, not `AGENT`.
**Fix:** Use `SNOWFLAKE.CORTEX.DATA_AGENT_RUN('agent_name', $$json_body$$)`.

### Pitfall 5: KPI values truncated (e.g., "$4,052,16...")
**Cause:** Large numbers overflow the metric card width.
**Fix:** Format with abbreviations:
```python
if val >= 1_000_000:
    display = f"${val / 1_000_000:.2f}M"
elif val >= 1_000:
    display = f"${val / 1_000:.1f}K"
```

### Pitfall 6: Agent response parsing fails
**Cause:** DATA_AGENT_RUN returns nested JSON with content[] array.
**Fix:** Parse the response correctly:
```python
resp = result[0]["RESPONSE"]
if isinstance(resp, str):
    resp = json.loads(resp)
for item in resp.get("content", []):
    if item.get("type") == "text":
        response_text += item.get("text", "")
```

---

## Architecture Summary

```
User Question
     │
     ▼
┌─────────────────────────────┐
│   Streamlit App (Chat Tab)  │
│   DATA_AGENT_RUN() call     │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Cortex Agent              │
│   (CLAIMS_FRAUD_TRIAGE)     │
│   Routes to tools based     │
│   on question intent        │
└──────┬──────────────┬───────┘
       │              │
       ▼              ▼
┌──────────────┐ ┌──────────────┐
│ Cortex       │ │ Cortex       │
│ Analyst      │ │ Search       │
│ (Structured) │ │ (Documents)  │
│              │ │              │
│ Claims,      │ │ Policy text, │
│ Policies,    │ │ Exclusions,  │
│ Customers,   │ │ Coverage     │
│ Billing      │ │ clauses      │
└──────┬───────┘ └──────┬───────┘
       │                │
       ▼                ▼
┌─────────────────────────────┐
│  Agent synthesizes both     │
│  into a risk verdict:       │
│  LOW / MEDIUM / HIGH RISK   │
│  with cited evidence        │
└─────────────────────────────┘
```

---

## Objects Created

| Object | Type | Location |
|--------|------|----------|
| INSURANCE_AI_HUB | Database | — |
| ANALYTICS | Schema | INSURANCE_AI_HUB |
| DOCUMENTS | Schema | INSURANCE_AI_HUB |
| DATA_QUALITY | Schema | INSURANCE_AI_HUB |
| CUSTOMERS | Table | ANALYTICS |
| POLICIES | Table | ANALYTICS |
| CLAIMS | Table | ANALYTICS |
| AGENTS | Table | ANALYTICS |
| BILLING | Table | ANALYTICS |
| AT_RISK_POLICIES | Table | ANALYTICS |
| POLICY_DOCUMENTS | Table | DOCUMENTS |
| DOCUMENT_CHUNKS | Table | DOCUMENTS |
| DQ_RULES | Table | DATA_QUALITY |
| DQ_RESULTS | Table | DATA_QUALITY |
| DQ_SCORES | Table | DATA_QUALITY |
| DQ_COLUMN_HEALTH | Table | DATA_QUALITY |
| INSURANCE_SEMANTIC_MODEL | Semantic View | ANALYTICS |
| POLICY_SEARCH_SVC | Cortex Search | DOCUMENTS |
| CLAIMS_FRAUD_TRIAGE_AGENT | Cortex Agent | ANALYTICS |
| CLAIMS_FRAUD_TRIAGE_COPILOT | Streamlit App | ANALYTICS |
