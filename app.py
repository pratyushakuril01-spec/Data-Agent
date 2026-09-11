"""
app.py
SPECTER.AI - Autonomous Ghost Subscription & Spend Leak Forensic Agent.
Powered by LangGraph Deep ReAct, E2B Code Interpreter Sandbox, and OpenRouter Multi-Model Routing.
"""

import os
import io
import json
import tempfile
import streamlit as st
import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.parser import StatementParser
from core.normalizer import MerchantNormalizer
from core.detector import SubscriptionDetector, RecurringItem
from core.email_generator import CancellationEmailGenerator
from core.e2b_sandbox import E2BSandboxManager
from core.langgraph_agent import LangGraphAuditAgent
from core.visualizer import (
    create_category_donut_chart,
    create_subscriptions_bar_chart,
    create_price_hike_comparison_chart
)

# Page configuration
st.set_page_config(
    page_title="SPECTER.AI | Forensic Spend Leak & Ghost Subscription Hunter",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern Cyber-Fintech Glassmorphism CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Main background accents */
    .stApp {
        background: radial-gradient(circle at 15% 10%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
                    radial-gradient(circle at 85% 60%, rgba(236, 72, 153, 0.05) 0%, transparent 45%),
                    #090D16;
    }

    /* Hero Header */
    .hero-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
    }
    .hero-title {
        font-size: 32px;
        font-weight: 800;
        background: linear-gradient(135deg, #F8FAFC 0%, #A5B4FC 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-subtitle {
        color: #94A3B8;
        font-size: 14px;
        margin-top: 6px;
        font-weight: 400;
    }
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34D399;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Metric Cards */
    .metric-card-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 24px;
    }
    .metric-card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 18px 20px;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #6366F1, transparent);
    }
    .metric-card.alert::before {
        background: linear-gradient(90deg, #EF4444, #F59E0B);
    }
    .metric-label {
        font-size: 11px;
        font-weight: 700;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }
    .metric-number {
        font-size: 28px;
        font-weight: 800;
        color: #F8FAFC;
        letter-spacing: -0.02em;
    }
    .metric-number.highlight {
        color: #F87171;
    }
    .metric-foot {
        font-size: 12px;
        color: #64748B;
        margin-top: 4px;
    }

    /* Subscription Item Card */
    .leak-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        backdrop-filter: blur(8px);
        transition: all 0.2s ease;
    }
    .leak-card:hover {
        border-color: rgba(99, 102, 241, 0.3);
        background: rgba(20, 29, 52, 0.7);
    }
    .badge-hike {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.35);
        color: #F87171;
        font-size: 10px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        letter-spacing: 0.05em;
    }
    .badge-trap {
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid rgba(245, 158, 11, 0.35);
        color: #FBBF24;
        font-size: 10px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        letter-spacing: 0.05em;
    }
    .badge-normal {
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(99, 102, 241, 0.35);
        color: #A5B4FC;
        font-size: 10px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        letter-spacing: 0.05em;
    }

    /* ReAct Terminal Trace */
    .trace-block {
        background: #0B0F19;
        border: 1px solid #1E293B;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        line-height: 1.6;
    }

    /* Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 8px 18px;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #4338CA 0%, #4F46E5 100%);
        box-shadow: 0 6px 16px rgba(79, 70, 229, 0.4);
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SIDEBAR CONFIGURATION & CONTROLS
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <span style="font-size:28px;">⚡</span>
        <div>
            <div style="font-size:18px;font-weight:800;letter-spacing:-0.02em;color:#F8FAFC;">SPECTER.AI</div>
            <div style="font-size:11px;color:#94A3B8;text-transform:uppercase;letter-spacing:0.06em;">Forensic Spend Radar</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div style='font-size:12px;font-weight:700;color:#CBD5E1;margin-bottom:6px;'>🧠 REASONING CORE (OPENROUTER)</div>", unsafe_allow_html=True)
    openrouter_key = st.text_input(
        "OpenRouter API Key",
        value=os.environ.get("OPENROUTER_API_KEY", ""),
        type="password",
        help="Access models like Claude 3.5 Sonnet, GPT-4o, and Gemini 2.0 Flash."
    )
    
    selected_model = st.selectbox(
        "Agent Model",
        options=[
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "google/gemini-2.0-flash-001",
            "deepseek/deepseek-chat",
            "meta-llama/llama-3.3-70b-instruct"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("<div style='font-size:12px;font-weight:700;color:#CBD5E1;margin-bottom:6px;'>📦 SANDBOX ENVIRONMENT (E2B)</div>", unsafe_allow_html=True)
    e2b_key = st.text_input(
        "E2B API Key",
        value=os.environ.get("E2B_API_KEY", ""),
        type="password",
        help="Executes forensic Python analysis scripts in an isolated cloud sandbox."
    )

    if e2b_key:
        st.markdown("<div class='status-pill'>🟢 E2B Cloud Active</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='background:rgba(245,158,11,0.1);color:#FBBF24;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600;display:inline-block;'>🟡 Local Sandbox Fallback</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div style='font-size:12px;font-weight:700;color:#CBD5E1;margin-bottom:6px;'>⚡ PRESET FORENSIC SCENARIOS</div>", unsafe_allow_html=True)
    col_demo1, col_demo2 = st.columns(2)
    load_personal = col_demo1.button("💳 Personal", use_container_width=True, help="Netflix hike, Prime, Spotify, Gym, Trial Trap")
    load_business = col_demo2.button("🏢 SaaS Team", use_container_width=True, help="AWS, Slack, GitHub, OpenAI, Dropbox hike")

    st.markdown("<br><div style='font-size:11px;color:#475569;text-align:center;'>SPECTER.AI v2.4 • Autonomous Audit Agent</div>", unsafe_allow_html=True)


# Session state persistence
if 'statement_path' not in st.session_state:
    st.session_state.statement_path = "sample_data/personal_chase_sample.csv"
if 'filename' not in st.session_state:
    st.session_state.filename = "personal_chase_sample.csv"
if 'audit_report' not in st.session_state:
    st.session_state.audit_report = None
if 'killed_services' not in st.session_state:
    st.session_state.killed_services = set()

if load_personal:
    st.session_state.statement_path = "sample_data/personal_chase_sample.csv"
    st.session_state.filename = "personal_chase_sample.csv"
    st.session_state.audit_report = None
    st.rerun()

if load_business:
    st.session_state.statement_path = "sample_data/small_business_amex_sample.csv"
    st.session_state.filename = "small_business_amex_sample.csv"
    st.session_state.audit_report = None
    st.rerun()


# =============================================================================
# HERO SECTION
# =============================================================================
st.markdown("""
<div class="hero-container">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
        <div>
            <div class="hero-title">
                <span>SPECTER.AI</span>
                <span class="status-pill">Forensic Mode Live</span>
            </div>
            <div class="hero-subtitle">
                Autonomous agent hunting phantom subscriptions, unmasking stealth price hikes, and recovering leaked cash via FTC-compliant letters.
            </div>
        </div>
        <div style="display:flex;gap:8px;">
            <span style="background:rgba(99,102,241,0.15);color:#A5B4FC;padding:4px 10px;border-radius:8px;font-size:12px;font-weight:600;font-family:monospace;">LangGraph ReAct</span>
            <span style="background:rgba(236,72,153,0.15);color:#F472B6;padding:4px 10px;border-radius:8px;font-size:12px;font-weight:600;font-family:monospace;">E2B Sandbox</span>
            <span style="background:rgba(16,185,129,0.15);color:#34D399;padding:4px 10px;border-radius:8px;font-size:12px;font-weight:600;font-family:monospace;">OpenRouter</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# UPLOAD / INGESTION ZONE
# =============================================================================
col_up1, col_up2 = st.columns([3, 1])
with col_up1:
    uploaded_file = st.file_uploader(
        "Upload Bank or Credit Card Statement (CSV / PDF)",
        type=["csv", "pdf"],
        label_visibility="collapsed"
    )
with col_up2:
    run_audit_btn = st.button("⚡ Scan For Leaks", type="primary", use_container_width=True)

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1])
    tfile.write(uploaded_file.read())
    tfile.flush()
    st.session_state.statement_path = tfile.name
    st.session_state.filename = uploaded_file.name
    st.session_state.audit_report = None

st.markdown(
    f"<div style='font-size:12px;color:#64748B;margin-top:-6px;margin-bottom:20px;'>"
    f"Current Statement Target: <b style='color:#94A3B8;'>{st.session_state.filename}</b>"
    f"</div>",
    unsafe_allow_html=True
)

# Execute Audit on Click or Initial Load
if run_audit_btn or st.session_state.audit_report is None:
    with st.spinner("🤖 SPECTER Agent reasoning & executing Python in E2B Sandbox..."):
        agent = LangGraphAuditAgent(
            openrouter_api_key=openrouter_key,
            e2b_api_key=e2b_key,
            model_name=selected_model
        )
        report = agent.run_audit(
            statement_path=st.session_state.statement_path,
            filename=st.session_state.filename
        )
        st.session_state.audit_report = report

report = st.session_state.audit_report

if report and report.total_transactions > 0:

    # Calculate active potential recovery
    marked_savings = sum(
        s.annualized_cost for s in report.detected_subscriptions if s.merchant in st.session_state.killed_services
    )

    # =========================================================================
    # GLOWING KPI RADAR
    # =========================================================================
    st.markdown("""
    <div class="metric-card-container">
        <div class="metric-card">
            <div class="metric-label">Monthly Burn Rate</div>
            <div class="metric-number">${:,.2f}<span style="font-size:14px;color:#94A3B8;">/mo</span></div>
            <div class="metric-foot">Active recurring drain</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Annualized Commitment</div>
            <div class="metric-number">${:,.2f}<span style="font-size:14px;color:#94A3B8;">/yr</span></div>
            <div class="metric-foot">12-Month recurring projection</div>
        </div>
        <div class="metric-card alert">
            <div class="metric-label">🚨 Identified Spend Leak</div>
            <div class="metric-number highlight">${:,.2f}<span style="font-size:14px;color:#FCA5A5;">/yr</span></div>
            <div class="metric-foot">Silent hikes + unmonitored traps</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Flagged Hikes & Traps</div>
            <div class="metric-number" style="color:#FBBF24;">{} <span style="font-size:14px;color:#94A3B8;">services</span></div>
            <div class="metric-foot">{} stealth hikes detected</div>
        </div>
    </div>
    """.format(
        report.recurring_monthly_burn,
        report.total_annualized_recurring,
        report.annualized_leak_waste,
        report.price_hikes_count + report.trial_traps_count,
        report.price_hikes_count
    ), unsafe_allow_html=True)

    # Recovery Tracker Banner if services toggled
    if marked_savings > 0:
        st.markdown(f"""
        <div style="background:linear-gradient(90deg, rgba(16,185,129,0.15), rgba(6,182,212,0.15));border:1px solid rgba(16,185,129,0.4);border-radius:12px;padding:12px 20px;display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
            <div style="display:flex;align-items:center;gap:10px;">
                <span style="font-size:22px;">💰</span>
                <span style="font-size:14px;font-weight:700;color:#34D399;">Potential Annual Cash Recoverable:</span>
            </div>
            <div style="font-size:20px;font-weight:800;color:#F8FAFC;">${marked_savings:,.2f} / year</div>
        </div>
        """, unsafe_allow_html=True)

    # =========================================================================
    # REASONING TRACE STREAM
    # =========================================================================
    with st.expander("🧠 LangGraph ReAct Forensic Reasoning & Sandbox Trace", expanded=False):
        st.markdown("<div style='font-size:12px;color:#94A3B8;margin-bottom:10px;'>Live execution log showing Thought -> Action -> Sandbox Observation:</div>", unsafe_allow_html=True)
        for step in report.react_trace:
            st.markdown(f"""
            <div class="trace-block">
                <div style="color:#818CF8;font-weight:700;margin-bottom:4px;">[STEP {step.step_number}] :: ACTION: {step.action}</div>
                <div style="color:#94A3B8;"><span style="color:#6366F1;">THOUGHT:</span> {step.thought}</div>
                <div style="color:#CBD5E1;margin-top:4px;"><span style="color:#10B981;">OBSERVATION:</span> {step.observation}</div>
            </div>
            """, unsafe_allow_html=True)

    # =========================================================================
    # INTERACTIVE VISUALIZATIONS
    # =========================================================================
    st.markdown("<div style='font-size:16px;font-weight:700;color:#F8FAFC;margin-top:10px;margin-bottom:12px;'>📊 Visual Spend Intelligence</div>", unsafe_allow_html=True)
    v_col1, v_col2 = st.columns([1, 1])
    with v_col1:
        cat_chart = create_category_donut_chart(report.categories_breakdown)
        st.plotly_chart(cat_chart, use_container_width=True)
    with v_col2:
        bar_chart = create_subscriptions_bar_chart(report.detected_subscriptions)
        st.plotly_chart(bar_chart, use_container_width=True)

    if report.price_hikes_count > 0:
        hike_chart = create_price_hike_comparison_chart(report.detected_subscriptions)
        st.plotly_chart(hike_chart, use_container_width=True)

    # =========================================================================
    # DETECTED LEAKS & LEGAL CANCELLATION COMMAND CENTER
    # =========================================================================
    st.markdown("---")
    st.markdown("<div style='font-size:18px;font-weight:800;color:#F8FAFC;margin-bottom:4px;'>🎯 Forensic Subscription Registry & Cancellation Hub</div>", unsafe_allow_html=True)
    st.caption("Review individual recurring commitments, trigger 1-click legal dispute letters, or mark services for termination.")

    # User details inputs for custom emails
    with st.expander("⚙️ Customize Notice Details (Your Name, Email, Card)", expanded=False):
        c_u1, c_u2, c_u3 = st.columns(3)
        user_name = c_u1.text_input("Full Name", value="Alex Morgan")
        user_email = c_u2.text_input("Billing Email", value="alex.morgan@example.com")
        user_last4 = c_u3.text_input("Card Last 4 Digits", value="4321")

    # Subscription Cards
    for idx, item in enumerate(report.detected_subscriptions):
        badge_html = (
            "<span class='badge-hike'>🚨 SILENT PRICE HIKE</span>" if item.has_price_hike
            else ("<span class='badge-trap'>⚠️ TRIAL TRAP</span>" if item.is_trial_rollover
            else "<span class='badge-normal'>✓ ACTIVE RECURRING</span>")
        )

        is_killed = item.merchant in st.session_state.killed_services

        st.markdown(f"""
        <div class="leak-card" style="{'border-left: 4px solid #EF4444;' if item.has_price_hike else ('border-left: 4px solid #F59E0B;' if item.is_trial_rollover else 'border-left: 4px solid #6366F1;')}">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <span style="font-size:18px;font-weight:700;color:#F8FAFC;">{item.merchant}</span>
                    {badge_html}
                </div>
                <div style="font-size:14px;color:#94A3B8;">
                    <b>${item.current_amount:.2f}</b> <span style="font-size:12px;">/{item.cadence.lower()}</span>
                    &nbsp;•&nbsp; <span style="color:#CBD5E1;">${item.annualized_cost:,.2f}/yr</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Alerts if hike / trap
        if item.has_price_hike:
            st.error(
                f"🚨 **Stealth Price Increase!** Increased from **${item.initial_amount:.2f}** to **${item.current_amount:.2f}** "
                f"(+${item.price_hike_amount:.2f} or +{item.price_hike_pct:.1f}%) on {item.hike_detected_date or item.last_date}. "
                f"Annual excess leak: **${item.annualized_leak_impact:,.2f}**."
            )

        if item.is_trial_rollover:
            st.warning(
                f"⚠️ **Intro Trial Rollover Trap!** Initial charge was only **${item.initial_amount:.2f}**, which automatically converted to **${item.current_amount:.2f}**."
            )

        # Card action buttons
        col_act1, col_act2 = st.columns([1, 5])
        with col_act1:
            if st.button("Mark for Kill" if not is_killed else "Undo Kill", key=f"kill_btn_{idx}"):
                if is_killed:
                    st.session_state.killed_services.remove(item.merchant)
                else:
                    st.session_state.killed_services.add(item.merchant)
                st.rerun()

        with col_act2:
            with st.expander(f"✉️ Generate Legal Cancellation Notice for {item.merchant}"):
                email_data = CancellationEmailGenerator.generate(
                    item=item,
                    user_name=user_name,
                    user_email=user_email,
                    account_last4=user_last4
                )
                st.text_input("Subject", value=email_data['subject'], key=f"subj_{idx}")
                st.text_area("Body", value=email_data['body'], height=200, key=f"body_{idx}")

                btn_c1, btn_c2 = st.columns([1, 3])
                with btn_c1:
                    st.markdown(
                        f"""<a href="{email_data['mailto_link']}" target="_blank">
                        <button style="background:#2563EB;color:white;border:none;padding:8px 16px;border-radius:6px;font-weight:600;cursor:pointer;">
                        📬 Launch in Mail App
                        </button></a>""",
                        unsafe_allow_html=True
                    )
                with btn_c2:
                    if item.cancellation_hint:
                        st.caption(f"Portal cancellation link: [https://{item.cancellation_hint}](https://{item.cancellation_hint})")

        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # E2B CODE INTERPRETER LIVE SANDBOX TERMINAL
    # =========================================================================
    st.markdown("---")
    st.markdown("<div style='font-size:16px;font-weight:700;color:#F8FAFC;margin-bottom:4px;'>💻 E2B Python Sandbox Console</div>", unsafe_allow_html=True)
    st.caption("Run ad-hoc Pandas data science queries on this statement inside an isolated E2B cloud environment:")

    sample_query = f"""# Inspect loaded statement DataFrame
import pandas as pd
df = pd.read_csv('{st.session_state.filename}')

# Find top 5 largest expenses
amt_col = [c for c in df.columns if 'amount' in c.lower()][0]
desc_col = [c for c in df.columns if 'desc' in c.lower()][0]
print("Top Outflows:")
print(df[[desc_col, amt_col]].sort_values(amt_col, ascending=False).head(5))
"""
    query_input = st.text_area("Python Script", value=sample_query, height=150)
    if st.button("▶️ Execute Python in E2B Sandbox"):
        sandbox_mgr = E2BSandboxManager(api_key=e2b_key)
        with open(st.session_state.statement_path, 'r', encoding='utf-8', errors='ignore') as f:
            sandbox_mgr.upload_file(st.session_state.filename, f.read())

        with st.spinner("Executing script in E2B Cloud Sandbox..."):
            res = sandbox_mgr.run_code(query_input)
            st.markdown(f"**Execution Runtime:** `{'E2B Cloud' if res.is_cloud_sandbox else 'Local Sandbox'}` (`{res.execution_time_seconds}s`)")
            if res.stdout:
                st.code(res.stdout, language="bash")
            if res.stderr:
                st.error(res.stderr)
            if res.error:
                st.error(res.error)

    # Export Report
    st.markdown("---")
    st.download_button(
        label="📥 Download Structured Forensic Audit Report (JSON)",
        data=json.dumps(report.to_dict(), indent=2),
        file_name=f"specter_audit_{st.session_state.filename}.json",
        mime="application/json"
    )

else:
    st.warning("No transactions detected. Please upload a valid statement or select a sample preset.")
