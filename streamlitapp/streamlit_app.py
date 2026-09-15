import streamlit as st
import json
import pandas as pd
from snowflake.snowpark.context import get_active_session

session = get_active_session()

st.set_page_config(page_title="Claims Fraud Triage Copilot", layout="wide")

AGENT_NAME = "INSURANCE_AI_HUB.ANALYTICS.CLAIMS_FRAUD_TRIAGE_AGENT"

st.markdown("""
<style>
    .kpi-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; text-align: center; }
    .kpi-value { font-size: 28px; font-weight: 700; color: #1e293b; }
    .kpi-label { font-size: 13px; color: #64748b; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.markdown("### Claims Fraud Triage Copilot")
    st.markdown("*One AI assistant that reads claims, policies, and documents together.*")
    st.markdown("---")
    st.markdown("**Powered by:**")
    st.markdown("- Cortex Agent (orchestration)")
    st.markdown("- Cortex Analyst (structured data)")
    st.markdown("- Cortex Search (policy docs)")
    st.markdown("---")
    st.markdown("**Quick questions:**")
    sample_questions = [
        "Is claim CLM-00050 suspicious?",
        "Top 10 highest fraud score open claims",
        "What exclusions apply to auto policies?",
        "Claims breakdown by type and avg fraud score",
    ]
    for q in sample_questions:
        if st.button(q, key=f"sq_{q}"):
            st.session_state["prefill_question"] = q

# ── Tabs ──
tab_chat, tab_dashboard, tab_dq = st.tabs(
    ["Fraud Triage Chat", "Claims Dashboard", "Data Quality"]
)

# ═══════════════════════════════════════════════════
# TAB 1: FRAUD TRIAGE CHAT (Cortex Agent)
# ═══════════════════════════════════════════════════
with tab_chat:
    st.markdown("### Ask about any claim, policy, or customer")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Input area using a form so Enter and button both work
    prefill = st.session_state.pop("prefill_question", None)
    with st.form(key="chat_form", clear_on_submit=True):
        prompt = st.text_input(
            "Ask a question",
            value=prefill or "",
            placeholder="e.g. Is claim CLM-00050 suspicious?",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Ask")

    # Process the question
    if submitted and prompt and prompt.strip():
        st.session_state.messages.append({"role": "user", "content": prompt.strip()})

        with st.spinner("Analyzing with Cortex Agent..."):
            try:
                messages_for_agent = [
                    {"role": m["role"], "content": [{"type": "text", "text": m["content"]}]}
                    for m in st.session_state.messages
                ]

                response_text = ""
                request_body = json.dumps({"messages": messages_for_agent})

                result = session.sql(f"""
                    SELECT TRY_PARSE_JSON(
                        SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
                            '{AGENT_NAME}',
                            $${request_body}$$
                        )
                    ) AS response
                """).collect()

                if result:
                    resp = result[0]["RESPONSE"]
                    if resp:
                        if isinstance(resp, str):
                            resp = json.loads(resp)
                        content_items = resp.get("content", [])
                        for item in content_items:
                            if item.get("type") == "text":
                                response_text += item.get("text", "")
                            elif item.get("type") == "tool_results":
                                for tool_result in item.get("tool_results", []):
                                    for c in tool_result.get("content", []):
                                        if c.get("type") == "text":
                                            response_text += "\n" + c.get("text", "")

                if not response_text:
                    response_text = "I couldn't generate a response. Please try rephrasing your question."

                st.session_state.messages.append({"role": "assistant", "content": response_text})

            except Exception as e:
                error_msg = f"Error communicating with agent: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

    # Display conversation history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'**You:** {msg["content"]}')
        else:
            st.markdown(f'**Copilot:** {msg["content"]}', unsafe_allow_html=True)
        st.markdown("---")

    # Clear chat
    if st.session_state.messages:
        if st.button("Clear conversation"):
            st.session_state.messages = []


# ═══════════════════════════════════════════════════
# TAB 2: CLAIMS DASHBOARD
# ═══════════════════════════════════════════════════
with tab_dashboard:
    st.markdown("### Claims Overview Dashboard")

    kpi_data = session.sql("""
        SELECT
            COUNT(*) AS total_claims,
            COUNT(CASE WHEN claim_status = 'Open' THEN 1 END) AS open_claims,
            ROUND(AVG(fraud_score), 3) AS avg_fraud_score,
            ROUND(SUM(COALESCE(approved_amount, 0)), 0) AS total_payouts,
            COUNT(CASE WHEN fraud_flag = TRUE THEN 1 END) AS fraud_flagged,
            ROUND(AVG(CASE WHEN days_to_resolve IS NOT NULL THEN days_to_resolve END), 1) AS avg_resolution_days
        FROM INSURANCE_AI_HUB.ANALYTICS.CLAIMS
    """).collect()[0]

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("Total Claims", f"{kpi_data['TOTAL_CLAIMS']:,}")
    with c2:
        st.metric("Open Claims", f"{kpi_data['OPEN_CLAIMS']:,}")
    with c3:
        st.metric("Avg Fraud Score", f"{kpi_data['AVG_FRAUD_SCORE']}")
    with c4:
        payout_val = float(kpi_data['TOTAL_PAYOUTS'] or 0)
        if payout_val >= 1_000_000:
            payout_str = f"${payout_val / 1_000_000:.2f}M"
        elif payout_val >= 1_000:
            payout_str = f"${payout_val / 1_000:.1f}K"
        else:
            payout_str = f"${payout_val:,.0f}"
        st.metric("Total Payouts", payout_str)
    with c5:
        st.metric("Fraud Flagged", f"{kpi_data['FRAUD_FLAGGED']:,}")
    with c6:
        st.metric("Avg Resolution (days)", f"{kpi_data['AVG_RESOLUTION_DAYS']}")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Claims by Type")
        df_type = session.sql("""
            SELECT claim_type AS CLAIM_TYPE, COUNT(*) AS COUNT,
                   ROUND(AVG(fraud_score), 3) AS AVG_FRAUD_SCORE,
                   ROUND(AVG(claim_amount), 0) AS AVG_AMOUNT
            FROM INSURANCE_AI_HUB.ANALYTICS.CLAIMS
            GROUP BY claim_type ORDER BY COUNT DESC
        """).to_pandas()
        st.bar_chart(df_type.set_index("CLAIM_TYPE")["COUNT"])
        st.dataframe(df_type)

    with col_right:
        st.markdown("#### Claims by Status")
        df_status = session.sql("""
            SELECT claim_status AS CLAIM_STATUS, COUNT(*) AS COUNT,
                   ROUND(SUM(claim_amount), 0) AS TOTAL_AMOUNT
            FROM INSURANCE_AI_HUB.ANALYTICS.CLAIMS
            GROUP BY claim_status ORDER BY COUNT DESC
        """).to_pandas()
        st.bar_chart(df_status.set_index("CLAIM_STATUS")["COUNT"])
        st.dataframe(df_status)

    st.markdown("---")

    col_l2, col_r2 = st.columns(2)

    with col_l2:
        st.markdown("#### Fraud Score Distribution")
        df_fraud = session.sql("""
            SELECT
                CASE
                    WHEN fraud_score < 0.3 THEN '1-Low (< 0.3)'
                    WHEN fraud_score < 0.5 THEN '2-Medium (0.3-0.5)'
                    WHEN fraud_score < 0.7 THEN '3-Elevated (0.5-0.7)'
                    ELSE '4-High (>= 0.7)'
                END AS RISK_BUCKET,
                COUNT(*) AS COUNT
            FROM INSURANCE_AI_HUB.ANALYTICS.CLAIMS
            GROUP BY RISK_BUCKET ORDER BY RISK_BUCKET
        """).to_pandas()
        st.bar_chart(df_fraud.set_index("RISK_BUCKET")["COUNT"])

    with col_r2:
        st.markdown("#### Top Friction Points")
        df_friction = session.sql("""
            SELECT friction_point AS FRICTION_POINT, COUNT(*) AS COUNT
            FROM INSURANCE_AI_HUB.ANALYTICS.CLAIMS
            WHERE friction_point IS NOT NULL
            GROUP BY friction_point ORDER BY COUNT DESC LIMIT 5
        """).to_pandas()
        st.bar_chart(df_friction.set_index("FRICTION_POINT")["COUNT"])

    st.markdown("---")
    st.markdown("#### High-Risk Claims (Fraud Score >= 0.7)")
    df_highrisk = session.sql("""
        SELECT c.claim_id, c.claim_type, c.claim_amount, c.fraud_score, c.claim_status,
               c.assigned_adjuster, c.priority, cu.first_name || ' ' || cu.last_name AS customer_name,
               cu.risk_tier
        FROM INSURANCE_AI_HUB.ANALYTICS.CLAIMS c
        LEFT JOIN INSURANCE_AI_HUB.ANALYTICS.CUSTOMERS cu ON c.customer_id = cu.customer_id
        WHERE c.fraud_score >= 0.7
        ORDER BY c.fraud_score DESC
        LIMIT 20
    """).to_pandas()
    st.dataframe(df_highrisk)


# ═══════════════════════════════════════════════════
# TAB 3: DATA QUALITY
# ═══════════════════════════════════════════════════
with tab_dq:
    st.markdown("### Data Quality Monitor")
    st.markdown("*Trust scoring — powered by INSURANCE_AI_HUB.DATA_QUALITY schema*")

    dq_latest = session.sql("""
        SELECT TABLE_NAME, OVERALL_SCORE, COMPLETENESS_SCORE, ACCURACY_SCORE,
               CONSISTENCY_SCORE, TIMELINESS_SCORE, TREND, SCORE_DATE
        FROM INSURANCE_AI_HUB.DATA_QUALITY.DQ_SCORES
        QUALIFY ROW_NUMBER() OVER (PARTITION BY TABLE_NAME ORDER BY SCORE_DATE DESC) = 1
        ORDER BY TABLE_NAME
    """).to_pandas()

    st.markdown("#### Latest Scores by Table")
    num_tables = len(dq_latest)
    if num_tables > 0:
        cols = st.columns(num_tables)
        for i, row in dq_latest.iterrows():
            with cols[i]:
                trend_icon = "UP" if row["TREND"] == "UP" else "DOWN" if row["TREND"] == "DOWN" else "FLAT"
                score = row["OVERALL_SCORE"]
                color = "#10b981" if score >= 90 else "#f59e0b" if score >= 75 else "#dc2626"
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">{row['TABLE_NAME']}</div>
                    <div class="kpi-value" style="color:{color}">{score}% ({trend_icon})</div>
                    <div class="kpi-label">
                        C:{row['COMPLETENESS_SCORE']}% | A:{row['ACCURACY_SCORE']}% |
                        T:{row['TIMELINESS_SCORE']}%
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    col_dq1, col_dq2 = st.columns(2)

    with col_dq1:
        st.markdown("#### DQ Score Trend Over Time")
        df_trend = session.sql("""
            SELECT SCORE_DATE, TABLE_NAME, OVERALL_SCORE
            FROM INSURANCE_AI_HUB.DATA_QUALITY.DQ_SCORES
            ORDER BY SCORE_DATE
        """).to_pandas()
        if not df_trend.empty:
            pivot = df_trend.pivot(index="SCORE_DATE", columns="TABLE_NAME", values="OVERALL_SCORE")
            st.line_chart(pivot)

    with col_dq2:
        st.markdown("#### Rule Results Summary")
        df_rules = session.sql("""
            SELECT r.RULE_NAME, r.SEVERITY, r.TARGET_TABLE, r.TARGET_COLUMN,
                   res.PASS_RATE, res.STATUS, res.FAILED_RECORDS
            FROM INSURANCE_AI_HUB.DATA_QUALITY.DQ_RULES r
            JOIN INSURANCE_AI_HUB.DATA_QUALITY.DQ_RESULTS res ON r.RULE_ID = res.RULE_ID
            QUALIFY ROW_NUMBER() OVER (PARTITION BY r.RULE_ID ORDER BY res.EXECUTION_DATE DESC) = 1
            ORDER BY res.PASS_RATE ASC
        """).to_pandas()
        st.dataframe(df_rules)

    st.markdown("---")
    st.markdown("#### Column Health")
    df_health = session.sql("""
        SELECT TABLE_NAME, COLUMN_NAME, HEALTH_STATUS, SCORE,
               NULL_PCT, DISTINCT_COUNT, DUPLICATE_PCT, OUTLIER_COUNT, FORMAT_VIOLATION_COUNT
        FROM INSURANCE_AI_HUB.DATA_QUALITY.DQ_COLUMN_HEALTH
        ORDER BY SCORE ASC
    """).to_pandas()
    st.dataframe(df_health)
