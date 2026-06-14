import os
import streamlit as st
from utils.data_loader import load_profile, get_available_mutations
from components.executive_summary import render_executive_summary
from components.agent_trace import render_agent_trace
from components.network_graph import render_network_graph
from components.intervention_engine import render_intervention_engine
from components.why_not_panel import render_why_not_panel
from components.evidence_timeline import render_evidence_timeline

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

st.sidebar.subheader("Select Genomic Mutation Profile")
available_mutations = get_available_mutations()

selected_mutation = st.sidebar.selectbox(
    "Active Profile",
    available_mutations,
    index=0,
    label_visibility="collapsed"
)

# Load selected mutation data
try:
    profile_data = load_profile(selected_mutation)
except Exception as e:
    st.error(f"Failed to load mutation profile: {e}")
    st.stop()

# Header Section
st.markdown(
    f"""
    <div style="margin-bottom: 25px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 15px;">
        <h1 style="margin: 0; font-family: 'Outfit', sans-serif; font-weight: 800; font-size: 2.1rem; color: #FFFFFF; letter-spacing: -0.8px;">
            Precision Oncology Multi-Agent Reasoning Platform
        </h1>
        <p style="margin: 5px 0 0 0; font-size: 0.95rem; color: #8892B0; font-family: 'Outfit', sans-serif;">
            Real-time genomic profiling, cell signaling network mapping, and therapeutic intervention simulation.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ── Row 1: Executive Summary + Hardware Telemetry ──────────────────────────
render_executive_summary(profile_data)

st.html('<div style="margin-bottom: 28px;"></div>')

# ── Row 2: Biological Signaling Network (full width) ────────────────────────
render_network_graph(profile_data)

st.html('<div style="margin-bottom: 28px;"></div>')

# ── Row 3: Pathway Intervention Engine + Agent Trace (side by side) ─────────
col_a, col_b = st.columns([1, 1], gap="large")

with col_a:
    render_intervention_engine(profile_data)

with col_b:
    render_agent_trace(profile_data)

st.html('<div style="margin-bottom: 28px;"></div>')

# ── Row 4: Clinical Exclusions + Evidence Registry (tabbed, full width) ──────
tab1, tab2 = st.tabs(["🚫  Exclusions & Contraindications", "📚  Reference Evidence Registry"])

with tab1:
    render_why_not_panel(profile_data)

with tab2:
    render_evidence_timeline(profile_data)

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
    PRECISION ONCOLOGY DEEP REASONER v1.0.0 &bull; HARDWARE: AMD INSTINCT MI300X &bull; ROCm v6.1
</div>
""")

