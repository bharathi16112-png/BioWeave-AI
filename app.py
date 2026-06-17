import os
import streamlit as st
from utils.data_loader import load_profile, get_available_mutations
from components.executive_summary import render_executive_summary
from components.agent_trace import render_agent_trace
from components.network_graph import render_network_graph
from components.intervention_engine import render_intervention_engine
from components.why_not_panel import render_why_not_panel
from components.evidence_timeline import render_evidence_timeline
from pipeline import run_multi_agent_pipeline

# Set up page configurations
st.set_page_config(
    page_title="Precision Oncology Platform",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load global CSS
def load_global_css():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(base_dir, "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_global_css()

# Sidebar - Profile Selection
st.sidebar.markdown(
    """
    <div style="text-align: center; margin-bottom: 25px;">
        <h2 style="font-family: 'Outfit', sans-serif; font-weight: 800; color: #FFFFFF; font-size: 1.5rem; letter-spacing: -0.5px; margin-bottom: 5px;">
            🧬 PRECISION LAB
        </h2>
        <span style="font-family: 'Space Mono', monospace; font-size: 0.75rem; color: #00D2D3; letter-spacing: 1.5px; text-transform: uppercase;">
            Multi-Agent Reasoner
        </span>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.title("🧬 Live Multimodal Intake")

uploaded_file = st.sidebar.file_uploader(
    "Upload Clinical Scan / Pathology Slide:", 
    type=["png", "jpg", "jpeg"]
)

if uploaded_file:
    st.sidebar.image(uploaded_file, caption="Uploaded Patient Slide Scan", use_container_width=True)
    st.sidebar.info("📷 Image attached for visual screening. Genomic text is required for live mutation detection.")

user_report = st.sidebar.text_area(
    "Paste Raw Genomic Text Report:",
    help="Required for live inference. Image alone cannot determine oncology mutations without a pathology-fine-tuned model.",
)

if st.sidebar.button("⚡ Run Real-Time Multi-Agent Trace", type="primary", use_container_width=True):
    if uploaded_file or user_report.strip():
        with st.spinner("Running Molecular Detective → Pathway Pathologist → Therapeutic Matchmaker..."):
            live_data = run_multi_agent_pipeline(user_report, uploaded_image=uploaded_file)
            if live_data:
                state = live_data.get("analysis_status", {}).get("analysis_state")
                if state == "insufficient_evidence":
                    st.session_state["live_profile"] = live_data
                    st.session_state["animate_trace"] = False
                    st.sidebar.warning(live_data["analysis_status"].get("message", "Insufficient evidence."))
                else:
                    st.session_state["live_profile"] = live_data
                    st.session_state["animate_trace"] = True
                    st.success("Live inference completed successfully.")
    else:
        st.sidebar.warning("Please upload an image or paste a genomic report first.")

st.sidebar.markdown("---")
st.sidebar.caption(
    "Free APIs: ClinVar (NCBI) · CIViC · OncoKB demo/public · "
    "Models: owkin/phikon · OpenMed NER"
)

st.sidebar.subheader("Or Select Demo Case")
available_mutations = get_available_mutations()

selected_mutation = st.sidebar.selectbox(
    "Active Profile",
    available_mutations,
    index=0,
    label_visibility="collapsed"
)

# Load selected mutation data
if "live_profile" in st.session_state:
    profile_data = st.session_state["live_profile"]
    _animate = st.session_state.pop("animate_trace", False)  # consume flag once
    st.sidebar.success("Displaying live inference results")
    if st.sidebar.button("Clear Live Profile", use_container_width=True):
        del st.session_state["live_profile"]
        st.rerun()
else:
    _animate = False
    try:
        profile_data = load_profile(selected_mutation)
    except Exception as e:
        st.error(f"Failed to load mutation profile: {e}")
        st.stop()

# Clinical disclaimer
st.warning(
    "**Research & demonstration use only.** This platform is not FDA-cleared, not validated "
    "for clinical decision-making, and must not be used to diagnose or treat patients. "
    "Live inference uses regex NER + curated knowledge bases; optional OncoKB and LLM enrichment "
    "require explicit configuration.",
    icon="⚠️",
)

analysis_state = profile_data.get("analysis_status", {}).get("analysis_state", "completed")
if analysis_state == "insufficient_evidence":
    st.error(profile_data.get("analysis_status", {}).get("message", "Insufficient evidence to proceed."))

# Header Section
st.markdown(
    """
    <div style="margin-bottom: 25px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 15px;">
        <h1 style="margin: 0; font-family: 'Outfit', sans-serif; font-weight: 800; font-size: 2.1rem; color: #FFFFFF; letter-spacing: -0.8px;">
            Precision Oncology Multi-Agent Reasoning Platform
        </h1>
        <p style="margin: 5px 0 0 0; font-size: 0.95rem; color: #8892B0; font-family: 'Outfit', sans-serif;">
            Live genomic NER, pathway mapping, OncoKB evidence enrichment, and intervention simulation.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ── Row 1: Executive Summary + Hardware Telemetry ──────────────────────────
render_executive_summary(profile_data)

if analysis_state == "completed":
    st.html('<div style="margin-bottom: 28px;"></div>')

    # ── Row 2: Biological Signaling Network (full width) ────────────────────────
    render_network_graph(profile_data)

    st.html('<div style="margin-bottom: 28px;"></div>')

    # ── Row 3: Pathway Intervention Engine + Agent Trace (side by side) ─────────
    col_a, col_b = st.columns([1, 1], gap="large")

    with col_a:
        render_intervention_engine(profile_data)

    with col_b:
        render_agent_trace(profile_data, animate=_animate)

    st.html('<div style="margin-bottom: 28px;"></div>')

    # ── Row 4: Clinical Exclusions + Evidence Registry (tabbed, full width) ──────
    tab1, tab2 = st.tabs(["🚫  Exclusions & Contraindications", "📚  Reference Evidence Registry"])

    with tab1:
        render_why_not_panel(profile_data)

    with tab2:
        render_evidence_timeline(profile_data)
else:
    st.html('<div style="margin-bottom: 28px;"></div>')
    render_agent_trace(profile_data, animate=False)

# ── Footer ────────────────────────────────────────────────────────────────────
st.html("""
<div style="
    margin-top: 50px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: 15px;
    text-align: center;
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    color: #505050;
    letter-spacing: 0.5px;
">
    PRECISION ONCOLOGY DEEP REASONER v1.1.0 &bull; RESEARCH USE ONLY &bull; LIVE INFERENCE ENABLED
</div>
""")

