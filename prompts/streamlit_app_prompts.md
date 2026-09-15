# Claims Fraud Triage Copilot — Complete Prompt Playbook

> A step-by-step guide to recreate the full solution from scratch using Cortex Code (CoCo).
> Follow the 3 prompts in order. Each builds on the previous one.

---

## What This Builds

An AI-powered insurance claims fraud triage system on Snowflake:

| Component | Count | Purpose |
|-----------|-------|---------|
| Tables with mock data | 12 | Across 3 schemas (ANALYTICS, DOCUMENTS, DATA_QUALITY) |
| Semantic View | 1 | Cortex Analyst — structured data queries |
| Cortex Search Service | 1 | Policy document retrieval |
| Cortex Agent | 1 | Orchestrates Analyst + Search into risk verdicts |
| Streamlit App | 1 | 3 tabs: Chat, Dashboard, Data Quality |
| Git Integration | 1 | GitHub-backed workspace for version control |

---

## Prerequisites

Run these **before** starting the prompts:

```sql
-- 1. Create a warehouse (if you don't have one)
CREATE WAREHOUSE IF NOT EXISTS AI_HUB_WH
  WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;

-- 2. Set your user defaults (REQUIRED for Cortex Agent)
ALTER USER <your_user> SET DEFAULT_WAREHOUSE = 'AI_HUB_WH';
ALTER USER <your_user> SET DEFAULT_ROLE = 'ACCOUNTADMIN';

-- 3. Enable cross-region inference (recommended for best model access)
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';
```

Replace `<your_user>` with your actual Snowflake username.

---

## PROMPT 1: Analyze the Architecture PDF (optional)

> Skip this if you don't have a PDF. Prompt 2 is self-contained.

### When to use
You have a design document (PDF) on a Snowflake stage and want CoCo to understand the architecture before building.

### Prompt
```
Analyze the pdf at '@"INSURANCE_AI_HUB"."DOCUMENTS"."TESTSTAGE"/flatten_Claims_Fraud_Triage_Copilot.pdf'

Summarize:
- The 3-schema data architecture
- Entity relationships between tables
- The end-to-end flow (user question → agent → tools → risk verdict)
- The worked example from the document
```

### What happens
CoCo uses `AI_PARSE_DOCUMENT` to extract and summarize the PDF. This gives it full context for Prompt 2.

---

## PROMPT 2: Build the Complete Solution

> This is the main prompt. It creates everything end-to-end in one shot.

### Prompt
```
Create an end-to-end Claims Fraud Triage Copilot solution for an insurance company on Snowflake.

## Database & Schema Setup
Create database INSURANCE_AI_HUB with 3 schemas:
- ANALYTICS — structured operational data
- DOCUMENTS — policy documents and embeddings
- DATA_QUALITY — trust scoring and monitoring

## Tables & Mock Data
Create all tables WITH realistic mock data inserted:

### ANALYTICS schema:
1. CUSTOMERS (200 rows) — CUSTOMER_ID, FIRST_NAME, LAST_NAME, DATE_OF_BIRTH, GENDER,
   EMAIL, PHONE, ADDRESS, CITY, STATE, ZIP_CODE, RISK_TIER (Low/Medium/High),
   CREDIT_SCORE, CUSTOMER_SINCE, SEGMENT (Individual/Family/Corporate)
2. POLICIES (300 rows) — POLICY_ID, CUSTOMER_ID, AGENT_ID,
   POLICY_TYPE (Health/Auto/Life/Home), POLICY_STATUS, START_DATE, END_DATE,
   PREMIUM_AMOUNT, COVERAGE_AMOUNT, DEDUCTIBLE, LOSS_RATIO,
   PLAN_TIER (Bronze/Silver/Gold/Platinum), PAYMENT_FREQUENCY, AUTO_RENEW
3. CLAIMS (400 rows) — CLAIM_ID, POLICY_ID, CUSTOMER_ID, CLAIM_DATE, CLAIM_TYPE,
   CLAIM_STATUS (Open/Approved/Denied/Under Investigation), CLAIM_AMOUNT,
   APPROVED_AMOUNT, FRAUD_FLAG, FRAUD_SCORE (0-1), ASSIGNED_ADJUSTER,
   RESOLUTION_DATE, DAYS_TO_RESOLVE, FRICTION_POINT, PRIORITY
4. AGENTS (20 rows) — AGENT_ID, AGENT_NAME, AGENT_TYPE, REGION, BRANCH,
   HIRE_DATE, LICENSE_NUMBER, SPECIALIZATION, PERFORMANCE_RATING, ACTIVE_FLAG
5. BILLING (500 rows) — BILLING_ID, POLICY_ID, CUSTOMER_ID, INVOICE_DATE, DUE_DATE,
   AMOUNT_DUE, AMOUNT_PAID, OUTSTANDING_BALANCE, PAYMENT_STATUS, PAYMENT_METHOD,
   PAYMENT_DATE, LATE_FEE
6. AT_RISK_POLICIES (165 rows) — RISK_ID, POLICY_ID, CUSTOMER_ID, RISK_CATEGORY,
   RISK_SCORE, REVENUE_AT_RISK, CHURN_PROBABILITY, LAST_INTERACTION_DATE,
   DAYS_SINCE_CONTACT, COMPLAINTS_COUNT, MISSED_PAYMENTS, RECOMMENDED_ACTION

### DOCUMENTS schema:
7. POLICY_DOCUMENTS (10 rows) — DOCUMENT_ID, POLICY_ID, DOCUMENT_TYPE,
   DOCUMENT_TITLE, FILE_NAME, CONTENT_TEXT, EXCLUSION_CLAUSES, COVERAGE_SUMMARY,
   PAGE_COUNT, DOCUMENT_STATUS
8. DOCUMENT_CHUNKS (25 rows) — CHUNK_ID, DOCUMENT_ID, CHUNK_INDEX, CHUNK_TEXT,
   SECTION_TITLE, TOKEN_COUNT

### DATA_QUALITY schema:
9. DQ_RULES (50 rows) — RULE_ID, RULE_NAME, RULE_DESCRIPTION, TARGET_TABLE,
   TARGET_COLUMN, RULE_TYPE (Completeness/Validity/Consistency/Timeliness),
   RULE_EXPRESSION, SEVERITY, IS_CRITICAL, THRESHOLD_PCT, ACTIVE_FLAG
10. DQ_RESULTS (40 rows) — RESULT_ID, RULE_ID, EXECUTION_DATE, TARGET_TABLE,
    TARGET_COLUMN, TOTAL_RECORDS, PASSED_RECORDS, FAILED_RECORDS, PASS_RATE, STATUS
11. DQ_SCORES (28 rows) — SCORE_ID, TABLE_NAME, SCHEMA_NAME, SCORE_DATE,
    OVERALL_SCORE, COMPLETENESS_SCORE, ACCURACY_SCORE, CONSISTENCY_SCORE,
    TIMELINESS_SCORE, RULES_PASSED, RULES_FAILED, TOTAL_RULES, TREND (UP/DOWN/FLAT)
12. DQ_COLUMN_HEALTH (28 rows) — HEALTH_ID, TABLE_NAME, COLUMN_NAME, CHECK_DATE,
    NULL_PCT, DISTINCT_COUNT, DUPLICATE_PCT, OUTLIER_COUNT,
    HEALTH_STATUS (Healthy/Warning/Critical), SCORE

## Semantic View
Create semantic view INSURANCE_AI_HUB.ANALYTICS.INSURANCE_SEMANTIC_MODEL covering all
ANALYTICS tables with:
- All relationships (Claims->Policies, Claims->Customers, Policies->Agents,
  Policies->Customers, Billing->Policies, AtRisk->Policies)
- Business metrics: TOTAL_PREMIUM, ACTIVE_POLICY_COUNT, AVG_LOSS_RATIO,
  AVG_FRAUD_SCORE, FRAUD_FLAGGED_COUNT, TOTAL_CLAIMS_PAID, AVG_RESOLUTION_DAYS,
  TOTAL_OUTSTANDING, TOTAL_REVENUE_AT_RISK
- Synonyms for business terms (e.g., "risk score" for FRAUD_SCORE)

## Cortex Search Service
Create INSURANCE_AI_HUB.DOCUMENTS.POLICY_SEARCH_SVC on POLICY_DOCUMENTS:
- Search column: concatenation of CONTENT_TEXT + EXCLUSION_CLAUSES + COVERAGE_SUMMARY
- Attribute columns: POLICY_ID, DOCUMENT_TYPE, DOCUMENT_TITLE
- Embedding model: snowflake-arctic-embed-m-v1.5
- Target lag: 1 minute
- Warehouse: AI_HUB_WH

## Cortex Agent
Create INSURANCE_AI_HUB.ANALYTICS.CLAIMS_FRAUD_TRIAGE_AGENT using CREATE AGENT with
FROM SPECIFICATION syntax:
- Tool 1: "InsuranceAnalyst" (type: cortex_analyst_text_to_sql) -> semantic view
- Tool 2: "PolicySearch" (type: cortex_search) -> search service
- IMPORTANT: Include execution_environment block with warehouse for the Analyst tool:
    execution_environment:
      type: warehouse
      warehouse: "AI_HUB_WH"
- Instructions: triage claims using BOTH tools, produce LOW/MEDIUM/HIGH risk verdicts
  with cited evidence
- Sample questions about claim investigation, fraud scores, policy exclusions

## Streamlit App
Create INSURANCE_AI_HUB.ANALYTICS.CLAIMS_FRAUD_TRIAGE_COPILOT with 3 tabs.

### CRITICAL: Warehouse-Runtime Streamlit Constraints
The Snowflake warehouse runtime uses an OLDER Streamlit version. You MUST follow these rules:

DO NOT USE (will cause runtime errors):
- st.chat_input() or st.chat_message()
- hide_index=True in st.dataframe()
- st.divider()
- type="primary" on st.button()
- color= parameter in st.bar_chart()
- style.map() on DataFrames
- st.experimental_rerun()
- use_container_width=True on st.button()

USE INSTEAD:
- st.form() with st.form_submit_button() for chat input (ensures Enter key works)
- st.markdown("---") instead of st.divider()
- st.bar_chart(df.set_index("COL")["VALUE"]) instead of st.bar_chart(df, x=, y=, color=)
- st.dataframe(df) without hide_index
- SNOWFLAKE.CORTEX.DATA_AGENT_RUN() to call the agent (NOT SNOWFLAKE.CORTEX.AGENT)
- Format large dollar amounts as $X.XXM or $X.XK to prevent truncation in st.metric()

### Tab 1 — Fraud Triage Chat:
- st.form wrapping text_input + form_submit_button (atomic submit on Enter or click)
- Calls DATA_AGENT_RUN, parses response content[] array for type="text" items
- Stores conversation in st.session_state.messages
- Sidebar with clickable sample questions

### Tab 2 — Claims Dashboard:
- 6 KPI metrics: Total Claims, Open Claims, Avg Fraud Score, Total Payouts ($XM format),
  Fraud Flagged, Avg Resolution Days
- 4 charts: Claims by Type, Claims by Status, Fraud Score Distribution, Top Friction Points
- Table: High-Risk Claims (fraud_score >= 0.7) joined with customer details

### Tab 3 — Data Quality:
- Color-coded score cards per table (green >= 90, yellow >= 75, red < 75)
- DQ score trend line chart over time (pivoted by TABLE_NAME)
- Rule results summary table
- Column health table
```

### What happens
CoCo will execute this in sequence: DDL -> INSERT mock data -> CREATE SEMANTIC VIEW -> CREATE CORTEX SEARCH SERVICE -> CREATE AGENT -> write Streamlit .py -> upload to stage -> CREATE STREAMLIT. Expect it to take several minutes.

---

## PROMPT 3: Verify the Agent Works End-to-End

### Prompt
```
Test the Cortex Agent by running this SQL and explain the results:

SELECT TRY_PARSE_JSON(
    SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
        'INSURANCE_AI_HUB.ANALYTICS.CLAIMS_FRAUD_TRIAGE_AGENT',
        $${"messages": [{"role": "user", "content": [{"type": "text", "text": "Is claim CLM-00050 suspicious? Should I fast-track or investigate? Give me claim details, relevant policy clauses, and a risk verdict."}]}]}$$
    )
) AS response;

Verify that:
1. The InsuranceAnalyst tool pulled structured claim/policy/customer data
2. The PolicySearch tool retrieved relevant policy exclusion clauses
3. The agent synthesized a risk verdict (LOW / MEDIUM / HIGH) with cited evidence
4. The Streamlit app loads without errors on all 3 tabs
```

### Expected result
The agent should return a detailed response showing:
- Structured facts (claim amount, fraud score, policy type, customer history)
- Retrieved policy clauses (exclusions, coverage terms)
- A risk verdict with recommended actions

---

## Common Pitfalls & Fixes

### 1. "Agent missing execution environment"

**Symptom:** Error code 391920 when calling DATA_AGENT_RUN.

**Cause:** The Cortex Analyst tool needs an explicit warehouse, AND the calling user must have a default warehouse set.

**Fix (both are required):**
```yaml
# In the agent YAML specification:
tool_resources:
  InsuranceAnalyst:
    semantic_view: "INSURANCE_AI_HUB.ANALYTICS.INSURANCE_SEMANTIC_MODEL"
    execution_environment:
      type: warehouse
      warehouse: "AI_HUB_WH"
```
```sql
-- On your Snowflake user:
ALTER USER <your_user> SET DEFAULT_WAREHOUSE = 'AI_HUB_WH';
```

### 2. "st.chat_input not found" / "hide_index unexpected keyword"

**Symptom:** `AttributeError: module 'streamlit' has no attribute 'chat_input'`

**Cause:** Warehouse-runtime Streamlit is version ~1.22 and lacks newer APIs.

**Fix:** See the "DO NOT USE / USE INSTEAD" table in Prompt 2. The most critical substitutions:
- `st.form()` + `st.form_submit_button()` replaces `st.chat_input()`
- Remove `hide_index=True` from all `st.dataframe()` calls
- `st.markdown("---")` replaces `st.divider()`

### 3. "Ask button does nothing" / Enter key unresponsive

**Symptom:** Typing a question and clicking Ask or pressing Enter produces no output.

**Cause:** `st.text_input()` + `st.button()` outside a form have a widget timing issue in older Streamlit — the button click triggers a rerun before the text value is committed.

**Fix:** Always wrap chat input in `st.form()`:
```python
with st.form(key="chat_form", clear_on_submit=True):
    prompt = st.text_input("Ask a question", label_visibility="collapsed")
    submitted = st.form_submit_button("Ask")

if submitted and prompt and prompt.strip():
    # process the question here
```

### 4. "SNOWFLAKE.CORTEX.AGENT unknown function"

**Symptom:** `SQL compilation error: Unknown user-defined function SNOWFLAKE.CORTEX.AGENT`

**Cause:** The function name is `DATA_AGENT_RUN`, not `AGENT`.

**Fix:**
```python
# WRONG
session.sql("SELECT SNOWFLAKE.CORTEX.AGENT(...)")

# CORRECT
session.sql("SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN('agent_name', $$json$$)")
```

### 5. KPI values truncated (e.g., "$4,052,16...")

**Symptom:** Large dollar amounts overflow the `st.metric()` card width and get cut off.

**Fix:** Format with human-readable abbreviations:
```python
payout_val = float(kpi_data['TOTAL_PAYOUTS'] or 0)
if payout_val >= 1_000_000:
    display = f"${payout_val / 1_000_000:.2f}M"
elif payout_val >= 1_000:
    display = f"${payout_val / 1_000:.1f}K"
else:
    display = f"${payout_val:,.0f}"
st.metric("Total Payouts", display)
```

### 6. Agent response parsing fails silently

**Symptom:** Chat shows "I couldn't generate a response" even though the agent ran.

**Cause:** `DATA_AGENT_RUN` returns a nested JSON structure. The text is inside `content[]` array items with `type: "text"`, not at the top level.

**Fix:**
```python
resp = result[0]["RESPONSE"]
if isinstance(resp, str):
    resp = json.loads(resp)
for item in resp.get("content", []):
    if item.get("type") == "text":
        response_text += item.get("text", "")
    elif item.get("type") == "tool_results":
        for tool_result in item.get("tool_results", []):
            for c in tool_result.get("content", []):
                if c.get("type") == "text":
                    response_text += "\n" + c.get("text", "")
```

---

## Architecture

```
User Question (Streamlit Chat)
     |
     v
+-------------------------------+
|  SNOWFLAKE.CORTEX             |
|  .DATA_AGENT_RUN()            |
+---------------+---------------+
                |
                v
+-------------------------------+
|  Cortex Agent                 |
|  CLAIMS_FRAUD_TRIAGE_AGENT    |
|  - Reads question intent      |
|  - Routes to 1 or both tools  |
+-------+--------------+-------+
        |              |
        v              v
+---------------+ +---------------+
| InsuranceAnalyst| | PolicySearch  |
| (Cortex Analyst)| | (Cortex Search)|
|                 | |               |
| Semantic View:  | | Search Service:|
| - CLAIMS        | | - POLICY_DOCS |
| - POLICIES      | | - Exclusions  |
| - CUSTOMERS     | | - Coverage    |
| - BILLING       | |   clauses     |
| - AGENTS        | |               |
| - AT_RISK       | |               |
+--------+--------+ +-------+------+
         |                  |
         v                  v
+-------------------------------+
|  Agent synthesizes both into  |
|  a risk verdict:              |
|                               |
|  LOW RISK  -> fast-track      |
|  MEDIUM RISK -> standard      |
|  HIGH RISK -> escalate to SIU |
|                               |
|  With cited data points and   |
|  policy clause references     |
+-------------------------------+
```

---

## Snowflake Objects Created

| Object | Type | Schema | Purpose |
|--------|------|--------|---------|
| INSURANCE_AI_HUB | Database | — | Project container |
| ANALYTICS | Schema | — | Structured operational data |
| DOCUMENTS | Schema | — | Policy documents & embeddings |
| DATA_QUALITY | Schema | — | Trust scoring & monitoring |
| CUSTOMERS | Table | ANALYTICS | 200 customer profiles |
| POLICIES | Table | ANALYTICS | 300 insurance policies |
| CLAIMS | Table | ANALYTICS | 400 claims with fraud scores |
| AGENTS | Table | ANALYTICS | 20 insurance agents |
| BILLING | Table | ANALYTICS | 500 billing records |
| AT_RISK_POLICIES | Table | ANALYTICS | 165 at-risk policy flags |
| POLICY_DOCUMENTS | Table | DOCUMENTS | 10 full policy contracts |
| DOCUMENT_CHUNKS | Table | DOCUMENTS | 25 chunked document sections |
| DQ_RULES | Table | DATA_QUALITY | 50 data quality rules |
| DQ_RESULTS | Table | DATA_QUALITY | 40 rule execution results |
| DQ_SCORES | Table | DATA_QUALITY | 28 table-level DQ scores |
| DQ_COLUMN_HEALTH | Table | DATA_QUALITY | 28 column health records |
| INSURANCE_SEMANTIC_MODEL | Semantic View | ANALYTICS | Cortex Analyst queries |
| POLICY_SEARCH_SVC | Cortex Search | DOCUMENTS | Policy clause retrieval |
| CLAIMS_FRAUD_TRIAGE_AGENT | Agent | ANALYTICS | Orchestration layer |
| CLAIMS_FRAUD_TRIAGE_COPILOT | Streamlit App | ANALYTICS | User interface |

---

## Original vs. Improved Prompts

The original session required **10+ back-and-forth prompts** to fix runtime errors:

| # | Original Issue | Root Cause |
|---|---------------|------------|
| 1 | `st.chat_input` not found | Older Streamlit runtime |
| 2 | `hide_index=True` error | Older Streamlit runtime |
| 3 | `color=` param error in bar_chart | Older Streamlit runtime |
| 4 | `SNOWFLAKE.CORTEX.AGENT` not found | Wrong function name |
| 5 | Agent "missing execution environment" | No warehouse in YAML |
| 6 | Ask button unresponsive | Widget timing bug |
| 7 | `st.experimental_rerun` crash | Not in warehouse runtime |
| 8 | KPI values truncated | No number formatting |

This playbook bakes **all fixes upfront** into 3 clean prompts with zero expected errors.
