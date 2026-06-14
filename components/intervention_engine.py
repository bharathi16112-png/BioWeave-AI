import streamlit as st
import time

def render_intervention_engine(profile_data):
    """Renders the pathway suppression animation engine mapping overall cascade scores."""
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h3 style="margin: 0; font-family: 'Outfit', sans-serif; font-weight: 600; color: #FFFFFF; font-size: 1.4rem;">
                Pathway Intervention Engine
            </h3>
            <p style="margin: 4px 0 0 0; font-size: 0.9rem; color: #A0A0A0; font-family: 'Outfit', sans-serif;">
                In-silico docking and inhibition animation. Simulates cascade phosphorylation suppression.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    engine_data = profile_data.get("pathway_intervention_engine", {})
    baseline = engine_data.get("baseline_pathway_activity_score", 1.0)
    post_interv = engine_data.get("predicted_post_intervention_activity_score", 0.0)
    rationale = engine_data.get("therapeutic_rationale", "N/A")
    
    summary = profile_data.get("executive_summary", {})
    drug_name = summary.get("recommended_therapy", "Targeted Agent")
    
    # Initialize session state for animation
    sim_key = f"sim_progress_{summary.get('mutation', 'default')}"
    if sim_key not in st.session_state:
        st.session_state[sim_key] = 0.0
        st.session_state[f"{sim_key}_running"] = False
        
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(
            f"""
            <div style="background: rgba(22,27,34,0.6); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 24px; height: 100%;">
                <h5 style="margin: 0 0 10px 0; color: #00D2D3; font-family: 'Outfit', sans-serif; text-transform: uppercase; font-size: 0.85rem;">
                    In-Silico Simulation
                </h5>
                <p style="font-size: 0.85rem; color: #A0A0A0; margin-bottom: 20px; font-family: 'Outfit', sans-serif;">
                    Dock <strong>{drug_name}</strong> to compute downstream kinase activity suppression.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Trigger buttons
        run_sim = st.button("⚡ Run Covalent Docking Sim", key=f"run_btn_{sim_key}", use_container_width=True)
        reset_sim = st.button("🔄 Reset Baseline Cascade", key=f"reset_btn_{sim_key}", use_container_width=True)
        
        if run_sim:
            st.session_state[f"{sim_key}_running"] = True
            st.session_state[sim_key] = 0.0
        
        if reset_sim:
            st.session_state[sim_key] = 0.0
            st.session_state[f"{sim_key}_running"] = False
            st.rerun()

    # Animation execution loop
    if st.session_state[f"{sim_key}_running"] and st.session_state[sim_key] < 1.0:
        time.sleep(0.08)
        st.session_state[sim_key] = min(1.0, st.session_state[sim_key] + 0.2)
        if st.session_state[sim_key] >= 1.0:
            st.session_state[f"{sim_key}_running"] = False
        st.rerun()

    progress = st.session_state[sim_key]
    
    # Calculate current score by interpolating between baseline and post_intervention
    current_score = baseline - (baseline - post_interv) * progress
    current_score_pct = int(current_score * 100)
    
    with col2:
        # Determine color for the bar
        if current_score > 0.7:
            bar_color = "linear-gradient(90deg, #FF4B4B 0%, #FF8E8E 100%)"
            status_text = "HYPERACTIVE PATHWAY"
            badge_color = "#FF4B4B"
        elif current_score > 0.3:
            bar_color = "linear-gradient(90deg, #FFAF66 0%, #FFBF88 100%)"
            status_text = "MODERATE ACTIVITY"
            badge_color = "#FFAF66"
        else:
            bar_color = "linear-gradient(90deg, #00D2D3 0%, #008283 100%)"
            status_text = "SUPPRESSED PATHWAY"
            badge_color = "#A8FFB2"
            
        st.markdown(
            f"""
            <div style="background: rgba(22,27,34,0.6); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 24px; height: 100%;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h5 style="margin: 0; color: #E6EDF3; font-family: 'Outfit', sans-serif; font-size: 0.95rem; text-transform: uppercase;">
                        Pathway Activity Index
                    </h5>
                    <span style="font-family: 'Space Mono', monospace; font-size: 0.8rem; color: {badge_color}; font-weight: bold;">
                        {status_text}
                    </span>
                </div>
                <div style="font-size: 2.8rem; font-weight: 800; color: #FFFFFF; font-family: 'Space Mono', monospace; margin: 10px 0;">
                    {current_score_pct}% <span style="font-size: 1rem; color: #A0A0A0; font-family: 'Outfit', sans-serif; font-weight: normal;">(Score: {current_score:.2f})</span>
                </div>
                <div style="background-color: rgba(255, 255, 255, 0.05); height: 10px; border-radius: 5px; overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.02); margin-bottom: 15px;">
                    <div style="width: {current_score_pct}%; background: {bar_color}; height: 100%; border-radius: 5px; transition: width 0.2s ease;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-family: 'Space Mono', monospace; font-size: 0.75rem; color: #707070;">
                    <span>Baseline: {int(baseline * 100)}%</span>
                    <span>Target Post-Drug: {int(post_interv * 100)}%</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
    
    # Rationale panel
    st.markdown(
        f"""
        <div style="background: rgba(22,27,34,0.6); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.08); border-left: 4px solid #00D2D3; border-radius: 12px; padding: 24px; margin-bottom: 16px;">
            <h5 style="margin: 0 0 8px 0; color: #00D2D3; font-family: 'Outfit', sans-serif; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px;">
                Therapeutic Mechanism & Rationale
            </h5>
            <p style="margin: 0; font-family: 'Outfit', sans-serif; font-size: 0.95rem; line-height: 1.5; color: #E6EDF3;">
                {rationale}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
