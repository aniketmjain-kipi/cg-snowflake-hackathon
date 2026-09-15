# Claims Fraud Triage Copilot — Feature Guide & Demo Storyline

---

## Part 1: Feature Guide

### App Overview

The Claims Fraud Triage Copilot is a unified AI assistant built on Snowflake that helps insurance claims adjusters fast-track honest claims and focus investigation on suspicious ones. It combines structured data analytics, policy document search, and AI-powered reasoning in a single Streamlit interface.

**Technology stack:** Snowflake Cortex Agent, Cortex Analyst, Cortex Search, Streamlit-in-Snowflake

---

### Sidebar — Navigation & Quick Access

| Element | Description |
|---------|-------------|
| **App title** | "Claims Fraud Triage Copilot" with a short tagline |
| **Powered by** | Lists the three Cortex services powering the app |
| **Quick questions** | 4 pre-built questions that submit instantly with one click — no need to type or press Ask |

**Quick questions available:**
1. "Is claim CLM-00050 suspicious?" — triggers a full fraud triage
2. "Top 10 highest fraud score open claims" — surfaces priority investigation targets
3. "What exclusions apply to auto policies?" — searches policy document clauses
4. "Claims breakdown by type and avg fraud score" — generates a summary table

---

### Tab 1: Fraud Triage Chat

**Purpose:** Conversational AI interface where adjusters ask natural-language questions about claims, policies, customers, or documents and receive structured risk assessments.

| Element | Description |
|---------|-------------|
| **Text input + Ask button** | Wrapped in a form — supports both Enter key and button click |
| **Conversation history** | Persistent within the session — shows full back-and-forth with the agent |
| **Clear conversation** | Resets the chat history for a fresh session |

**How it works under the hood:**
1. User question is sent to `SNOWFLAKE.CORTEX.DATA_AGENT_RUN()`
2. The Cortex Agent decides which tools to invoke:
   - **InsuranceAnalyst** (Cortex Analyst) — generates and runs SQL against the semantic view to pull structured facts (claim amounts, fraud scores, policy details, customer history)
   - **PolicySearch** (Cortex Search) — retrieves relevant policy clauses, exclusions, and coverage terms from indexed policy documents
3. The agent synthesizes results from both tools into a plain-English response with a risk verdict (LOW / MEDIUM / HIGH) and cited evidence

**Types of questions it handles:**
- Claim-specific triage: "Is claim CLM-00050 suspicious?"
- Aggregation queries: "What is the average fraud score by claim type?"
- Policy document search: "What exclusions apply to life insurance policies?"
- Combined analysis: "Show me all open claims with fraud score above 0.7 that are on auto policies"

---

### Tab 2: Claims Dashboard

**Purpose:** At-a-glance operational overview of the claims portfolio with KPIs, charts, and a high-risk claims watchlist.

**Last refreshed timestamp** — shows when data was last queried, updates on every page interaction.

#### KPI Row (6 metrics)

| # | Metric | Value Example | What It Measures | Why It Matters | SQL Logic |
|---|--------|--------------|------------------|----------------|-----------|
| 1 | **Total Claims** | 400 | Total number of claims filed across all types and statuses | Gives the overall volume of the claims portfolio. A sudden spike could indicate a catastrophic event, seasonal pattern, or data ingestion issue. | `COUNT(*)` from CLAIMS |
| 2 | **Open Claims** | 87 | Claims currently in "Open" status awaiting adjuster review | Measures the active workload. If this number grows faster than resolutions, the team is falling behind. Adjusters use this to gauge staffing needs. | `COUNT(CASE WHEN claim_status = 'Open')` |
| 3 | **Avg Fraud Score** | 0.389 | Mean fraud probability score across all claims (scale: 0.0 = clean, 1.0 = certain fraud) | The portfolio-level fraud temperature. If this rises week over week, it may signal a new fraud ring, a model recalibration, or data quality issues feeding the scoring model. | `AVG(fraud_score)` |
| 4 | **Total Payouts** | $4.05M | Sum of all approved claim amounts, formatted with M/K suffix | The dollar exposure — how much the company has paid out. Tracked against premiums collected to monitor loss ratios. Displayed as abbreviated amount (e.g., $4.05M) to prevent UI truncation. | `SUM(COALESCE(approved_amount, 0))` |
| 5 | **Fraud Flagged** | 32 | Count of claims where the fraud detection model set fraud_flag = TRUE | Direct measure of how many claims the model considers suspicious. Compare against actual investigation outcomes to calibrate model precision. If this number is high relative to Total Claims, the threshold may need adjustment. | `COUNT(CASE WHEN fraud_flag = TRUE)` |
| 6 | **Avg Resolution (days)** | 18.7 | Mean calendar days from claim filing to resolution (for resolved claims only) | The speed-of-service metric. Insurance regulators often set SLA thresholds (e.g., 30 days). A rising average signals bottlenecks — cross-reference with the Friction Points chart below to identify root causes. | `AVG(days_to_resolve)` where not null |

**How to read these KPIs together:**

- **Healthy portfolio:** Open Claims is low relative to Total Claims, Avg Fraud Score is stable, Avg Resolution is within SLA.
- **Staffing concern:** Open Claims rising + Avg Resolution increasing = adjusters are overwhelmed.
- **Fraud concern:** Fraud Flagged count rising + Avg Fraud Score climbing = potential new fraud pattern. Drill into the High-Risk Claims table below.
- **Financial concern:** Total Payouts growing faster than premium revenue (check POLICIES table) = deteriorating loss ratio.

#### Charts Row 1

| Chart | Type | What it shows |
|-------|------|---------------|
| **Claims by Type** | Bar chart + data table | Distribution of claims across types (Medical, Accident, Theft, etc.) with average fraud score and claim amount per type |
| **Claims by Status** | Bar chart + data table | Distribution across statuses (Open, Approved, Denied, Under Investigation) with total dollar amounts |

#### Charts Row 2

| Chart | Type | What it shows |
|-------|------|---------------|
| **Fraud Score Distribution** | Bar chart | Claims bucketed into 4 risk tiers: Low (< 0.3), Medium (0.3-0.5), Elevated (0.5-0.7), High (>= 0.7) |
| **Top Friction Points** | Bar chart | Top 5 bottlenecks causing claim processing delays (e.g., "Missing documentation", "Third-party delay", "Adjuster backlog") |

#### High-Risk Claims Table

| Column | Description |
|--------|-------------|
| CLAIM_ID | Unique claim identifier |
| CLAIM_TYPE | Type of claim (Medical, Accident, Theft, etc.) |
| CLAIM_AMOUNT | Dollar amount claimed |
| FRAUD_SCORE | AI-generated fraud probability (0-1) |
| CLAIM_STATUS | Current status |
| ASSIGNED_ADJUSTER | Name of the claims adjuster |
| PRIORITY | Low / Medium / High |
| CUSTOMER_NAME | Full name (joined from CUSTOMERS table) |
| RISK_TIER | Customer risk classification |

Filters: fraud_score >= 0.7, sorted by fraud score descending, limited to top 20.

---

### Tab 3: Data Quality

**Purpose:** Trust and reliability monitoring for the underlying data — ensures adjusters and the AI agent are working from accurate, complete, and timely data.

**Last refreshed timestamp** — shows when DQ data was last queried.

#### Latest Scores by Table (color-coded cards)

One card per monitored table, showing:

| Element | Description |
|---------|-------------|
| **Table name** | Which table is being scored |
| **Overall score** | Percentage score with color coding: Green (>= 90%), Yellow (>= 75%), Red (< 75%) |
| **Trend** | UP / DOWN / FLAT compared to previous period |
| **Sub-scores** | C = Completeness, A = Accuracy, T = Timeliness |

Tables monitored: CUSTOMERS, POLICIES, CLAIMS, BILLING (and others in the DATA_QUALITY schema).

#### DQ Score Trend Over Time

- **Type:** Multi-line chart
- **X-axis:** Score date
- **Y-axis:** Overall DQ score (0-100%)
- **Lines:** One per table, showing score trajectory over weekly checks
- **Use case:** Spot regressions — if a table's score drops, investigate before it affects AI accuracy

#### Rule Results Summary

| Column | Description |
|--------|-------------|
| RULE_NAME | Name of the DQ rule (e.g., NOT_NULL_CUSTOMER_ID, VALID_POLICY_TYPE) |
| SEVERITY | Critical / High / Medium / Low |
| TARGET_TABLE | Which table the rule monitors |
| TARGET_COLUMN | Which column is checked |
| PASS_RATE | Percentage of records passing the rule |
| STATUS | PASS or FAIL |
| FAILED_RECORDS | Count of records that failed |

Sorted by pass rate ascending (worst rules first).

#### Column Health

| Column | Description |
|--------|-------------|
| TABLE_NAME | Source table |
| COLUMN_NAME | Column being profiled |
| HEALTH_STATUS | Healthy / Warning / Critical |
| SCORE | Health score (0-100) |
| NULL_PCT | Percentage of null values |
| DISTINCT_COUNT | Number of unique values |
| DUPLICATE_PCT | Percentage of duplicates |
| OUTLIER_COUNT | Number of statistical outliers |
| FORMAT_VIOLATION_COUNT | Values failing format validation |

Sorted by score ascending (unhealthiest columns first).

---

## Part 2: Demo Video Storyline

### Title Slide
> "Claims Fraud Triage Copilot — One AI assistant that reads claims, policies, and documents together"

---

### Scene 1: The Problem (30 seconds)

**Narration:**
> "In a typical insurance company, claim reviews are slow because knowledge lives in three silos. Structured data — claim amounts, fraud scores, policy status — sits in database tables. Policy contracts with coverage and exclusion clauses live in long PDFs. And whether the underlying data is even reliable? Usually only the data team knows."
>
> "The result: every claim gets the same manual review, investigators rely on gut instinct, genuine customers wait weeks, and fraud teams are expensive to scale."

**Visual:** Show the architecture slide from the PDF — three silos converging into one.

---

### Scene 2: The Solution Overview (20 seconds)

**Narration:**
> "The Claims Fraud Triage Copilot solves this with one chat interface powered by three Snowflake Cortex services. Cortex Analyst queries structured claims data. Cortex Search retrieves policy document clauses. And a Cortex Agent orchestrates both, reasoning over the combined results to produce a risk verdict — all inside Snowflake, with no new infrastructure."

**Visual:** Open the Streamlit app, show the sidebar with "Powered by" section.

---

### Scene 3: Live Demo — Fraud Triage Chat (2-3 minutes)

**Narration:**
> "Let's say I'm a claims adjuster, and I just received claim CLM-00050. I need to decide: fast-track it, or investigate?"

**Action:** Click the sidebar quick question "Is claim CLM-00050 suspicious?"

**Narration (while loading):**
> "Behind the scenes, the Cortex Agent is doing three things: querying the claims, policies, and customers tables through the semantic view, searching the policy document index for relevant clauses, and then reasoning over both to produce a verdict."

**Narration (when results appear):**
> "And here's the verdict: HIGH RISK. The agent found three red flags:"
> 1. "The fraud score is 0.67 — elevated above our threshold"
> 2. "This is a Medical claim filed against a Homeowners policy — a coverage type mismatch that's a classic fraud signal"
> 3. "The claim was already approved for $17,708 despite being fraud-flagged"
>
> "The agent recommends escalating to the Special Investigations Unit and reviewing the payout for possible recovery. It cites the specific policy exclusion clause it found. An adjuster gets all of this in seconds, not hours."

**Action:** Ask a follow-up: "What is the full claim history for customer CUST-00072?"

**Narration:**
> "And because it's conversational, I can ask follow-ups. Here I'm checking if this customer has a pattern of suspicious filings."

---

### Scene 4: Claims Dashboard (1-2 minutes)

**Action:** Click the "Claims Dashboard" tab.

**Narration:**
> "The Claims Dashboard gives me the operational picture at a glance. Six KPIs across the top: 400 total claims, with the average fraud score, total payouts at $4.05 million, and 32 claims flagged for fraud."

**Action:** Scroll to the charts.

> "Claims by Type shows me the distribution — Medical and Accident claims dominate. Claims by Status shows how many are Open versus Approved or Under Investigation."
>
> "The Fraud Score Distribution is key: I can see how many claims fall in each risk bucket. And Top Friction Points tells me where the bottlenecks are — missing documentation, third-party delays, adjuster backlog."

**Action:** Scroll to the High-Risk Claims table.

> "At the bottom, a watchlist: the top 20 claims with fraud scores above 0.7, joined with customer details. This is where an investigation manager starts their day — sorted by the highest fraud scores first."

---

### Scene 5: Data Quality Monitor (1 minute)

**Action:** Click the "Data Quality" tab.

**Narration:**
> "Before trusting any AI-generated verdict, you need to trust the data. The Data Quality tab monitors every table powering the copilot."
>
> "Each table gets a color-coded score card. Green means healthy — 90% or above. Yellow is a warning. Red means something needs attention."

**Action:** Point to the trend chart.

> "The trend chart shows quality over time. If the CLAIMS table score suddenly drops, we know the AI's fraud scores might be unreliable that week."

**Action:** Point to the Rule Results table.

> "Individual DQ rules are tracked — things like 'Customer ID must not be null' or 'Policy type must be a valid value.' The worst-performing rules surface first."

**Action:** Point to Column Health.

> "And at the column level, I can see null rates, duplicate percentages, outlier counts, and format violations. This is the trust layer that makes the entire copilot reliable."

---

### Scene 6: Closing (20 seconds)

**Narration:**
> "To summarize: the Claims Fraud Triage Copilot delivers three things."
> 1. "80% of claims are typically low-risk and can be fast-tracked — the copilot identifies them instantly"
> 2. "100% consistency — every claim gets the same checks, every time, regardless of investigator workload"
> 3. "Zero new infrastructure — built entirely on Snowflake Cortex, Streamlit, and data already in your warehouse"
>
> "One chat box. Three Cortex specialists. Faster payouts for honest customers. Sharper detection for fraud."

**Visual:** Return to the chat tab showing the risk verdict.

---

### Demo Script — Quick Reference

| Time | Scene | Action | Key Talking Point |
|------|-------|--------|-------------------|
| 0:00 | Problem | Show architecture slide | 3 silos slow every claim review |
| 0:30 | Solution | Open app, show sidebar | One AI, three Cortex services, zero infra |
| 0:50 | Chat demo | Click "Is claim CLM-00050 suspicious?" | Agent uses Analyst + Search, produces HIGH RISK verdict |
| 2:00 | Chat follow-up | Type a follow-up question | Conversational, multi-turn context |
| 2:30 | Dashboard | Switch to Claims Dashboard tab | KPIs, 4 charts, high-risk watchlist |
| 3:30 | Data Quality | Switch to Data Quality tab | Trust layer — scores, trends, rules, column health |
| 4:30 | Closing | Return to chat tab | 80% fast-track, 100% consistent, 0 new infra |
