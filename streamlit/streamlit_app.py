import streamlit as st
import json
import re
import pandas as pd
from datetime import datetime
from snowflake.snowpark.context import get_active_session

session = get_active_session()

st.set_page_config(page_title="ClaimSure", layout="wide")

AGENT_NAME = "INSURANCE_AI_HUB.ANALYTICS.CLAIMS_FRAUD_TRIAGE_AGENT"

# ═══════════════════════════════════════════════════
# GLOBAL CSS
# ═══════════════════════════════════════════════════
st.markdown("""
<style>
    /* ── KPI Cards ── */
    .kpi-card {
        border-radius: 10px; padding: 18px 12px; text-align: center;
        border: 1px solid #e2e8f0; background: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .kpi-icon { font-size: 22px; margin-bottom: 4px; }
    .kpi-value { font-size: 26px; font-weight: 700; color: #1e293b; margin: 2px 0; }
    .kpi-label { font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-accent-blue { border-left: 4px solid #3b82f6; }
    .kpi-accent-amber { border-left: 4px solid #f59e0b; }
    .kpi-accent-red { border-left: 4px solid #ef4444; }
    .kpi-accent-green { border-left: 4px solid #10b981; }
    .kpi-accent-purple { border-left: 4px solid #8b5cf6; }
    .kpi-accent-teal { border-left: 4px solid #14b8a6; }

    /* ── Chat Bubbles ── */
    .chat-user {
        background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px;
        padding: 12px 16px; margin: 8px 0;
    }
    .chat-user-label { font-size: 11px; font-weight: 600; color: #3b82f6; text-transform: uppercase; margin-bottom: 4px; }
    .chat-bot {
        background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #14b8a6;
        border-radius: 10px; padding: 12px 16px; margin: 8px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .chat-bot-label { font-size: 11px; font-weight: 600; color: #14b8a6; text-transform: uppercase; margin-bottom: 4px; }

    /* ── Risk Verdicts ── */
    .verdict-high {
        background: #fef2f2; border: 1px solid #fecaca; border-left: 4px solid #dc2626;
        border-radius: 8px; padding: 10px 14px; margin: 10px 0; font-weight: 600; color: #991b1b;
    }
    .verdict-medium {
        background: #fffbeb; border: 1px solid #fde68a; border-left: 4px solid #f59e0b;
        border-radius: 8px; padding: 10px 14px; margin: 10px 0; font-weight: 600; color: #92400e;
    }
    .verdict-low {
        background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #22c55e;
        border-radius: 8px; padding: 10px 14px; margin: 10px 0; font-weight: 600; color: #166534;
    }

    /* ── DQ Score Cards ── */
    .dq-card {
        border-radius: 10px; padding: 16px; text-align: center;
        border: 1px solid #e2e8f0; background: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .dq-table-name { font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 8px; }
    .dq-score { font-size: 28px; font-weight: 700; margin: 4px 0; }
    .dq-bar-bg { background: #e5e7eb; border-radius: 6px; height: 8px; width: 100%; margin: 8px 0; }
    .dq-bar-fill { border-radius: 6px; height: 8px; }
    .dq-sub { font-size: 11px; color: #64748b; }
    .dq-trend-up { color: #16a34a; font-weight: 600; }
    .dq-trend-down { color: #dc2626; font-weight: 600; }

    /* ── Status Badges ── */
    .badge-pass {
        background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 10px;
        font-size: 11px; font-weight: 600; display: inline-block;
    }
    .badge-fail {
        background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 10px;
        font-size: 11px; font-weight: 600; display: inline-block;
    }
    .badge-healthy { background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
    .badge-warning { background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
    .badge-critical { background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }

    /* ── Insight box ── */
    .insight-box {
        background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px;
        padding: 10px 14px; margin: 10px 0; font-size: 14px; color: #0c4a6e;
    }

    /* ── Section headers ── */
    .section-header {
        font-size: 16px; font-weight: 600; color: #1e293b;
        border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; margin: 16px 0 10px 0;
    }

    /* ── Quick question pills ── */
    .qq-container { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 16px 0; }

    /* ── Chat input area ── */
    .chat-input-wrapper {
        background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;
        padding: 16px; margin-bottom: 16px;
    }
    .chat-input-label {
        font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px;
    }

    /* ── Conversation area ── */
    .convo-header {
        font-size: 14px; font-weight: 600; color: #64748b; text-transform: uppercase;
        letter-spacing: 0.5px; margin: 12px 0 8px 0;
    }

    /* ── Pulsing thinking indicator ── */
    @keyframes pulse-dot {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40% { transform: scale(1); opacity: 1; }
    }
    .thinking-container {
        display: flex; align-items: center; gap: 6px;
        padding: 14px 18px; margin: 8px 0;
        background: #f0fdfa; border: 1px solid #99f6e4; border-left: 4px solid #14b8a6;
        border-radius: 10px;
    }
    .thinking-label { font-size: 13px; color: #0f766e; font-weight: 600; margin-right: 4px; }
    .thinking-dots { display: flex; gap: 4px; align-items: center; }
    .thinking-dot {
        width: 8px; height: 8px; border-radius: 50%; background: #14b8a6;
        animation: pulse-dot 1.4s infinite ease-in-out;
    }
    .thinking-dot:nth-child(2) { animation-delay: 0.2s; }
    .thinking-dot:nth-child(3) { animation-delay: 0.4s; }

    /* ── Sidebar icons ── */
    .sidebar-section {
        font-size: 13px; font-weight: 600; color: #334155;
        margin: 4px 0 6px 0; letter-spacing: 0.3px;
    }
    .sidebar-item { font-size: 13px; color: #475569; margin: 2px 0; }

    /* ── Two-metric chart legend ── */
    .chart-legend {
        display: flex; gap: 16px; margin: 4px 0 8px 0; font-size: 12px; color: #64748b;
    }
    .legend-dot {
        width: 10px; height: 10px; border-radius: 50%; display: inline-block;
        margin-right: 4px; vertical-align: middle;
    }

    /* ── Dark theme overrides — removed, keeping light theme ── */
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.image("image.png")
    st.markdown("*One AI assistant that reads claims, policies, and documents together.*")
    st.markdown("---")
    st.markdown("""
    <div class="sidebar-section">&#9889; Powered by</div>
    <div class="sidebar-item">&#8226; Cortex Agent <span style="color:#94a3b8;">(orchestration)</span></div>
    <div class="sidebar-item">&#8226; Cortex Analyst <span style="color:#94a3b8;">(structured data)</span></div>
    <div class="sidebar-item">&#8226; Cortex Search <span style="color:#94a3b8;">(policy docs)</span></div>
    """, unsafe_allow_html=True)

# ── Tabs ──
tab_chat, tab_dashboard, tab_dq = st.tabs(
    ["\U0001F50D ClaimSure Agent", "\U0001F4CA Claims Dashboard", "\u2705 Data Quality Dashboard"]
)

# ═══════════════════════════════════════════════════
# TAB 1: CLAIMSURE AGENT
# ═══════════════════════════════════════════════════
with tab_chat:
    st.markdown("""
    <div style="margin-bottom:4px;">
        <span style="font-size:24px; font-weight:700; color:#1e293b;">ClaimSure Agent</span>
    </div>
    <div style="font-size:14px; color:#64748b; margin-bottom:16px;">
        Ask about any claim, policy, or customer. The Cortex Agent queries structured data and policy documents simultaneously, then synthesizes a risk verdict with cited evidence.
    </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    def call_agent(question):
        st.session_state.messages.append({"role": "user", "content": question})
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("""
        <div class="thinking-container">
            <span class="thinking-label">ClaimSure Copilot is analyzing</span>
            <div class="thinking-dots">
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
            </div>
        </div>""", unsafe_allow_html=True)
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
                    for item in resp.get("content", []):
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
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)}"})
        finally:
            thinking_placeholder.empty()

    def highlight_risk_verdicts(text):
        text = re.sub(r'(HIGH\s*RISK[^<\n]*)', r'<div class="verdict-high">\1</div>', text, flags=re.IGNORECASE)
        text = re.sub(r'(MEDIUM\s*RISK[^<\n]*)', r'<div class="verdict-medium">\1</div>', text, flags=re.IGNORECASE)
        text = re.sub(r'(LOW\s*RISK[^<\n]*)', r'<div class="verdict-low">\1</div>', text, flags=re.IGNORECASE)
        return text

    auto_q = st.session_state.pop("auto_submit", None)
    if auto_q:
        call_agent(auto_q)

    # Quick questions above input
    st.markdown('<div style="font-size:13px; font-weight:600; color:#475569; margin-bottom:6px;">Try a quick question:</div>', unsafe_allow_html=True)
    sample_questions = [
        "Is claim CLM-00050 suspicious?",
        "Top 10 highest fraud score open claims",
        "What exclusions apply to auto policies?",
        "Claims breakdown by type and avg fraud score",
    ]
    qcols = st.columns(len(sample_questions))
    for i, q in enumerate(sample_questions):
        with qcols[i]:
            if st.button(q, key=f"sq_{q}"):
                st.session_state["auto_submit"] = q

    # Input form
    st.markdown('<div class="chat-input-wrapper">', unsafe_allow_html=True)
    with st.form(key="chat_form", clear_on_submit=True):
        prompt = st.text_input(
            "Ask a question",
            placeholder="Type your question here and press Enter or click Ask...",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Ask")
    st.markdown('</div>', unsafe_allow_html=True)

    if submitted and prompt and prompt.strip():
        call_agent(prompt.strip())

    # Conversation history
    if st.session_state.messages:
        st.markdown('<div class="convo-header">Conversation</div>', unsafe_allow_html=True)
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-user">
                    <div class="chat-user-label">You</div>
                    {msg["content"]}
                </div>""", unsafe_allow_html=True)
            else:
                styled = highlight_risk_verdicts(msg["content"])
                st.markdown(f"""
                <div class="chat-bot">
                    <div class="chat-bot-label">ClaimSure Copilot</div>
                    {styled}
                </div>""", unsafe_allow_html=True)
        if st.button("Clear conversation"):
            st.session_state.messages = []
    else:
        st.markdown("""
        <div style="text-align:center; padding:40px 20px; color:#94a3b8;">
            <div style="font-size:36px; margin-bottom:8px;">&#128269;</div>
            <div style="font-size:15px; font-weight:500;">No conversation yet</div>
            <div style="font-size:13px; margin-top:4px;">Click a quick question above or type your own to get started.</div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# TAB 2: CLAIMS DASHBOARD
# ═══════════════════════════════════════════════════
with tab_dashboard:
    st.markdown("""
    <div style="margin-bottom:4px;">
        <span style="font-size:24px; font-weight:700; color:#1e293b;">Claims Overview Dashboard</span>
    </div>
    <div style="font-size:14px; color:#64748b; margin-bottom:16px;">
        Real-time portfolio snapshot &mdash; KPIs, claim distributions, fraud score analysis, processing bottlenecks, and a high-risk watchlist for investigation prioritization.
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"Last refreshed: {datetime.now().strftime('%b %d, %Y %I:%M:%S %p')}")

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

    # Format payouts
    payout_val = float(kpi_data['TOTAL_PAYOUTS'] or 0)
    if payout_val >= 1_000_000:
        payout_str = f"${payout_val / 1_000_000:.2f}M"
    elif payout_val >= 1_000:
        payout_str = f"${payout_val / 1_000:.1f}K"
    else:
        payout_str = f"${payout_val:,.0f}"

    # Fraud rate
    total = int(kpi_data['TOTAL_CLAIMS'])
    flagged = int(kpi_data['FRAUD_FLAGGED'])
    fraud_pct = round(flagged / total * 100, 1) if total > 0 else 0

    # Styled KPI cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    kpis = [
        (c1, "kpi-accent-blue",   "Total Claims",         f"{total:,}",                               "All claims filed"),
        (c2, "kpi-accent-amber",  "Open Claims",          f"{kpi_data['OPEN_CLAIMS']:,}",             "Awaiting review"),
        (c3, "kpi-accent-purple", "Avg Fraud Score",      f"{kpi_data['AVG_FRAUD_SCORE']}",           "Portfolio risk (0-1)"),
        (c4, "kpi-accent-teal",   "Total Payouts",        payout_str,                                  "Approved amounts"),
        (c5, "kpi-accent-red",    "Fraud Flagged",        f"{flagged:,}",                              f"{fraud_pct}% of portfolio"),
        (c6, "kpi-accent-green",  "Avg Resolution",       f"{kpi_data['AVG_RESOLUTION_DAYS']} days",  "Mean time to close"),
    ]
    for col, accent, label, value, sublabel in kpis:
        with col:
            st.markdown(f"""
            <div class="kpi-card {accent}">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-label" style="font-size:11px; margin-top:2px;">{sublabel}</div>
            </div>""", unsafe_allow_html=True)

    # Insight text
    open_claims = int(kpi_data['OPEN_CLAIMS'])
    st.markdown(f"""
    <div class="insight-box">
        <strong>Insight:</strong> {flagged} claims flagged for fraud ({fraud_pct}% of portfolio).
        {open_claims} claims are still Open awaiting adjuster review.
        Average resolution is {kpi_data['AVG_RESOLUTION_DAYS']} days.
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="section-header">Claims by Type</div>', unsafe_allow_html=True)
        df_type = session.sql("""
            SELECT claim_type AS CLAIM_TYPE, COUNT(*) AS COUNT,
                   ROUND(AVG(fraud_score), 3) AS AVG_FRAUD_SCORE,
                   ROUND(AVG(claim_amount), 0) AS AVG_AMOUNT
            FROM INSURANCE_AI_HUB.ANALYTICS.CLAIMS
            GROUP BY claim_type ORDER BY COUNT DESC
        """).to_pandas()
        # Two-metric HTML bar chart: count bars + fraud score overlay
        max_count = df_type["COUNT"].max() if not df_type.empty else 1
        chart_html = '<div style="margin:8px 0;">'
        chart_html += """<div class="chart-legend">
            <span><span class="legend-dot" style="background:#3b82f6;"></span> Claim Count</span>
            <span><span class="legend-dot" style="background:#f59e0b;"></span> Avg Fraud Score</span>
        </div>"""
        for _, row in df_type.iterrows():
            pct = row["COUNT"] / max_count * 100
            fs = float(row["AVG_FRAUD_SCORE"])
            fs_pct = fs * 100
            fs_color = "#dc2626" if fs >= 0.5 else "#f59e0b" if fs >= 0.3 else "#22c55e"
            chart_html += f'''
            <div style="margin:6px 0;">
                <div style="font-size:12px; font-weight:600; color:#334155; margin-bottom:2px;">{row["CLAIM_TYPE"]}</div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <div style="flex:1; background:#e5e7eb; border-radius:4px; height:20px; position:relative;">
                        <div style="width:{pct}%; background:#3b82f6; height:100%; border-radius:4px;"></div>
                    </div>
                    <span style="font-size:12px; color:#475569; min-width:30px;">{row["COUNT"]}</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px; margin-top:2px;">
                    <div style="flex:1; background:#f5f5f4; border-radius:4px; height:10px; position:relative;">
                        <div style="width:{fs_pct}%; background:{fs_color}; height:100%; border-radius:4px;"></div>
                    </div>
                    <span style="font-size:11px; color:{fs_color}; font-weight:600; min-width:30px;">{fs}</span>
                </div>
            </div>'''
        chart_html += '</div>'
        st.markdown(chart_html, unsafe_allow_html=True)
        # Formatted table
        df_type_display = df_type.copy()
        df_type_display["AVG_AMOUNT"] = df_type_display["AVG_AMOUNT"].apply(lambda x: f"${x:,.0f}")
        st.dataframe(df_type_display)

    with col_right:
        st.markdown('<div class="section-header">Claims by Status</div>', unsafe_allow_html=True)
        df_status = session.sql("""
            SELECT claim_status AS CLAIM_STATUS, COUNT(*) AS COUNT,
                   ROUND(SUM(claim_amount), 0) AS TOTAL_AMOUNT
            FROM INSURANCE_AI_HUB.ANALYTICS.CLAIMS
            GROUP BY claim_status ORDER BY COUNT DESC
        """).to_pandas()
        st.bar_chart(df_status.set_index("CLAIM_STATUS")["COUNT"])
        df_status_display = df_status.copy()
        df_status_display["TOTAL_AMOUNT"] = df_status_display["TOTAL_AMOUNT"].apply(lambda x: f"${x:,.0f}")
        st.dataframe(df_status_display)

    st.markdown("---")

    col_l2, col_r2 = st.columns(2)

    with col_l2:
        st.markdown('<div class="section-header">Fraud Score Distribution</div>', unsafe_allow_html=True)
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
        st.markdown('<div class="section-header">Top Friction Points</div>', unsafe_allow_html=True)
        df_friction = session.sql("""
            SELECT friction_point AS FRICTION_POINT, COUNT(*) AS COUNT
            FROM INSURANCE_AI_HUB.ANALYTICS.CLAIMS
            WHERE friction_point IS NOT NULL
            GROUP BY friction_point ORDER BY COUNT DESC LIMIT 5
        """).to_pandas()
        st.bar_chart(df_friction.set_index("FRICTION_POINT")["COUNT"])

    st.markdown("---")
    st.markdown('<div class="section-header">High-Risk Claims (Fraud Score >= 0.7)</div>', unsafe_allow_html=True)
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

    # Build HTML table with color-coded fraud scores
    risk_html = '<table style="width:100%; border-collapse:collapse; font-size:13px;">'
    risk_html += '<tr style="background:#f1f5f9; font-weight:600;">'
    for col_name in ["Claim ID", "Type", "Amount", "Fraud Score", "Status", "Adjuster", "Priority", "Customer", "Risk Tier"]:
        risk_html += f'<td style="padding:8px; border-bottom:2px solid #e2e8f0;">{col_name}</td>'
    risk_html += '</tr>'
    for _, row in df_highrisk.iterrows():
        fs = float(row["FRAUD_SCORE"])
        if fs >= 0.85:
            fs_color = "#dc2626"; fs_bg = "#fef2f2"
        elif fs >= 0.75:
            fs_color = "#ea580c"; fs_bg = "#fff7ed"
        else:
            fs_color = "#d97706"; fs_bg = "#fffbeb"
        risk_html += '<tr style="border-bottom:1px solid #f1f5f9;">'
        risk_html += f'<td style="padding:7px; font-weight:600;">{row["CLAIM_ID"]}</td>'
        risk_html += f'<td style="padding:7px;">{row["CLAIM_TYPE"]}</td>'
        risk_html += f'<td style="padding:7px;">${float(row["CLAIM_AMOUNT"]):,.0f}</td>'
        risk_html += f'<td style="padding:7px; background:{fs_bg}; color:{fs_color}; font-weight:700; border-radius:4px; text-align:center;">{fs:.2f}</td>'
        risk_html += f'<td style="padding:7px;">{row["CLAIM_STATUS"]}</td>'
        risk_html += f'<td style="padding:7px;">{row["ASSIGNED_ADJUSTER"]}</td>'
        risk_html += f'<td style="padding:7px;">{row["PRIORITY"]}</td>'
        risk_html += f'<td style="padding:7px;">{row["CUSTOMER_NAME"]}</td>'
        risk_html += f'<td style="padding:7px;">{row["RISK_TIER"]}</td>'
        risk_html += '</tr>'
    risk_html += '</table>'
    st.markdown(risk_html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# TAB 3: DATA QUALITY
# ═══════════════════════════════════════════════════
with tab_dq:
    st.markdown("""
    <div style="margin-bottom:4px;">
        <span style="font-size:24px; font-weight:700; color:#1e293b;">Data Quality Dashboard</span>
    </div>
    <div style="font-size:14px; color:#64748b; margin-bottom:16px;">
        Trust layer for the AI copilot &mdash; tracks completeness, accuracy, consistency, and timeliness across all source tables so verdicts are grounded in reliable data.
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"Last refreshed: {datetime.now().strftime('%b %d, %Y %I:%M:%S %p')}")

    dq_latest = session.sql("""
        SELECT TABLE_NAME, OVERALL_SCORE, COMPLETENESS_SCORE, ACCURACY_SCORE,
               CONSISTENCY_SCORE, TIMELINESS_SCORE, TREND, SCORE_DATE
        FROM INSURANCE_AI_HUB.DATA_QUALITY.DQ_SCORES
        QUALIFY ROW_NUMBER() OVER (PARTITION BY TABLE_NAME ORDER BY SCORE_DATE DESC) = 1
        ORDER BY TABLE_NAME
    """).to_pandas()

    st.markdown('<div class="section-header">Latest Scores by Table</div>', unsafe_allow_html=True)
    num_tables = len(dq_latest)
    if num_tables > 0:
        cols = st.columns(num_tables)
        for i, row in dq_latest.iterrows():
            with cols[i]:
                score = float(row["OVERALL_SCORE"])
                color = "#16a34a" if score >= 90 else "#d97706" if score >= 75 else "#dc2626"
                bar_color = "#22c55e" if score >= 90 else "#f59e0b" if score >= 75 else "#ef4444"
                trend = row["TREND"]
                if trend == "UP":
                    trend_html = '<span class="dq-trend-up">&#9650; UP</span>'
                elif trend == "DOWN":
                    trend_html = '<span class="dq-trend-down">&#9660; DOWN</span>'
                else:
                    trend_html = '<span style="color:#64748b;">&#9654; FLAT</span>'

                st.markdown(f"""
                <div class="dq-card">
                    <div class="dq-table-name">{row['TABLE_NAME']}</div>
                    <div class="dq-score" style="color:{color}">{score}%</div>
                    <div class="dq-bar-bg"><div class="dq-bar-fill" style="width:{score}%; background:{bar_color};"></div></div>
                    <div>{trend_html}</div>
                    <div class="dq-sub" style="margin-top:6px;">
                        C: {row['COMPLETENESS_SCORE']}% &middot;
                        A: {row['ACCURACY_SCORE']}% &middot;
                        T: {row['TIMELINESS_SCORE']}%
                    </div>
                </div>""", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown('<div class="section-header">DQ Score Trend Over Time</div>', unsafe_allow_html=True)
    df_trend = session.sql("""
        SELECT SCORE_DATE, TABLE_NAME, OVERALL_SCORE
        FROM INSURANCE_AI_HUB.DATA_QUALITY.DQ_SCORES
        ORDER BY SCORE_DATE
    """).to_pandas()
    if not df_trend.empty:
        pivot = df_trend.pivot(index="SCORE_DATE", columns="TABLE_NAME", values="OVERALL_SCORE")
        st.line_chart(pivot)

    st.markdown("---")

    st.markdown('<div class="section-header">Rule Results Summary</div>', unsafe_allow_html=True)
    df_rules = session.sql("""
        SELECT r.RULE_NAME, r.SEVERITY, r.TARGET_TABLE, r.TARGET_COLUMN,
               res.PASS_RATE, res.STATUS, res.FAILED_RECORDS
        FROM INSURANCE_AI_HUB.DATA_QUALITY.DQ_RULES r
        JOIN INSURANCE_AI_HUB.DATA_QUALITY.DQ_RESULTS res ON r.RULE_ID = res.RULE_ID
        QUALIFY ROW_NUMBER() OVER (PARTITION BY r.RULE_ID ORDER BY res.EXECUTION_DATE DESC) = 1
        ORDER BY res.PASS_RATE ASC
    """).to_pandas()

    # HTML table with status badges
    rules_html = '<div style="max-height:450px; overflow-y:auto;">'
    rules_html += '<table style="width:100%; border-collapse:collapse; font-size:13px;">'
    rules_html += '<tr style="background:#f1f5f9; font-weight:600;">'
    for h in ["Rule", "Severity", "Table", "Column", "Pass Rate", "Status", "Failed"]:
        rules_html += f'<td style="padding:8px; border-bottom:2px solid #e2e8f0;">{h}</td>'
    rules_html += '</tr>'
    for _, r in df_rules.iterrows():
        badge = '<span class="badge-pass">PASS</span>' if r["STATUS"] == "PASS" else '<span class="badge-fail">FAIL</span>'
        pr = float(r["PASS_RATE"])
        pr_color = "#16a34a" if pr >= 95 else "#d97706" if pr >= 80 else "#dc2626"
        rules_html += f'''<tr style="border-bottom:1px solid #f1f5f9;">
            <td style="padding:7px; font-weight:500;">{r["RULE_NAME"]}</td>
            <td style="padding:7px;">{r["SEVERITY"]}</td>
            <td style="padding:7px;">{r["TARGET_TABLE"]}</td>
            <td style="padding:7px;">{r["TARGET_COLUMN"]}</td>
            <td style="padding:7px; color:{pr_color}; font-weight:600;">{pr}%</td>
            <td style="padding:7px;">{badge}</td>
            <td style="padding:7px;">{int(r["FAILED_RECORDS"])}</td>
        </tr>'''
    rules_html += '</table></div>'
    st.markdown(rules_html, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-header">Column Health</div>', unsafe_allow_html=True)
    df_health = session.sql("""
        SELECT TABLE_NAME, COLUMN_NAME, HEALTH_STATUS, SCORE,
               NULL_PCT, DISTINCT_COUNT, DUPLICATE_PCT, OUTLIER_COUNT, FORMAT_VIOLATION_COUNT
        FROM INSURANCE_AI_HUB.DATA_QUALITY.DQ_COLUMN_HEALTH
        ORDER BY SCORE ASC
    """).to_pandas()

    # HTML table with health badges and score gradient
    health_html = '<div style="max-height:450px; overflow-y:auto;">'
    health_html += '<table style="width:100%; border-collapse:collapse; font-size:13px;">'
    health_html += '<tr style="background:#f1f5f9; font-weight:600;">'
    for h in ["Table", "Column", "Health", "Score", "Null %", "Distinct", "Dup %", "Outliers", "Format Err"]:
        health_html += f'<td style="padding:8px; border-bottom:2px solid #e2e8f0;">{h}</td>'
    health_html += '</tr>'
    for _, r in df_health.iterrows():
        hs = r["HEALTH_STATUS"]
        if hs == "Healthy":
            badge = '<span class="badge-healthy">Healthy</span>'
        elif hs == "Warning":
            badge = '<span class="badge-warning">Warning</span>'
        else:
            badge = '<span class="badge-critical">Critical</span>'
        sc = float(r["SCORE"])
        sc_color = "#16a34a" if sc >= 90 else "#d97706" if sc >= 75 else "#dc2626"
        health_html += f'''<tr style="border-bottom:1px solid #f1f5f9;">
            <td style="padding:7px;">{r["TABLE_NAME"]}</td>
            <td style="padding:7px; font-weight:500;">{r["COLUMN_NAME"]}</td>
            <td style="padding:7px;">{badge}</td>
            <td style="padding:7px; color:{sc_color}; font-weight:700;">{sc}</td>
            <td style="padding:7px;">{r["NULL_PCT"]}%</td>
            <td style="padding:7px;">{int(r["DISTINCT_COUNT"])}</td>
            <td style="padding:7px;">{r["DUPLICATE_PCT"]}%</td>
            <td style="padding:7px;">{int(r["OUTLIER_COUNT"])}</td>
            <td style="padding:7px;">{int(r["FORMAT_VIOLATION_COUNT"])}</td>
        </tr>'''
    health_html += '</table></div>'
    st.markdown(health_html, unsafe_allow_html=True)
