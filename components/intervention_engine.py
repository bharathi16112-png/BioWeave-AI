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
    
    # ── Session-state: store the *actual score* (not a 0-1 ratio) ──
    sim_key = f"sim_score_{summary.get('mutation', 'default')}"
    if sim_key not in st.session_state:
        st.session_state[sim_key] = baseline          # start at baseline
        st.session_state[f"{sim_key}_running"] = False

    # ── Helper: render the score card HTML into any slot ────────────
    def _render_score_card(slot, score: float):
        pct = int(score * 100)
        if score > 0.7:
            bar_color   = "linear-gradient(90deg, #FF4B4B 0%, #FF8E8E 100%)"
            status_text = "HYPERACTIVE PATHWAY"
            badge_color = "#FF4B4B"
        elif score > 0.3:
            bar_color   = "linear-gradient(90deg, #FFAA00 0%, #FFBF88 100%)"
            status_text = "MODERATE ACTIVITY"
            badge_color = "#FFAA00"
        else:
            bar_color   = "linear-gradient(90deg, #00F0FF 0%, #008283 100%)"
            status_text = "SUPPRESSED PATHWAY"
            badge_color = "#A8FFB2"
        slot.markdown(
            f"""
            <div style="background: rgba(22,27,34,0.6); backdrop-filter: blur(12px);
                        border: 1px solid rgba(255,255,255,0.08); border-radius: 12px;
                        padding: 24px; height: 100%;">
                <div style="display: flex; justify-content: space-between;
                            align-items: center; margin-bottom: 12px;">
                    <h5 style="margin: 0; color: #E6EDF3; font-family: 'Outfit', sans-serif;
                               font-size: 0.95rem; text-transform: uppercase;">
                        Pathway Activity Index
                    </h5>
                    <span style="font-family: 'Space Mono', monospace; font-size: 0.8rem;
                                 color: {badge_color}; font-weight: bold;">
                        {status_text}
                    </span>
                </div>
                <div style="font-size: 2.8rem; font-weight: 800; color: #FFFFFF;
                            font-family: 'Space Mono', monospace; margin: 10px 0;">
                    {pct}%
                    <span style="font-size: 1rem; color: #A0A0A0;
                                 font-family: 'Outfit', sans-serif; font-weight: normal;">
                        (Score: {score:.2f})
                    </span>
                </div>
                <div style="background-color: rgba(255,255,255,0.05); height: 10px;
                            border-radius: 5px; overflow: hidden;
                            border: 1px solid rgba(255,255,255,0.02); margin-bottom: 15px;">
                    <div style="width: {pct}%; background: {bar_color}; height: 100%;
                                border-radius: 5px; transition: width 0.04s linear;"></div>
                </div>
                <div style="display: flex; justify-content: space-between;
                            font-family: 'Space Mono', monospace;
                            font-size: 0.75rem; color: #707070;">
                    <span>Baseline: {int(baseline * 100)}%</span>
                    <span>Target Post-Drug: {int(post_interv * 100)}%</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Layout ───────────────────────────────────────────────────────
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(
            f"""
            <div style="background: rgba(22,27,34,0.6); backdrop-filter: blur(12px);
                        border: 1px solid rgba(255,255,255,0.08); border-radius: 12px;
                        padding: 24px; height: 100%;">
                <h5 style="margin: 0 0 10px 0; color: #00F0FF; font-family: 'Outfit', sans-serif;
                           text-transform: uppercase; font-size: 0.85rem;">
                    In-Silico Simulation
                </h5>
                <p style="font-size: 0.85rem; color: #A0A0A0; margin-bottom: 20px;
                          font-family: 'Outfit', sans-serif;">
                    Dock <strong>{drug_name}</strong> to compute downstream kinase
                    activity suppression.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        run_sim   = st.button("⚡ Run Covalent Docking Sim",  key=f"run_btn_{sim_key}",   use_container_width=True)
        reset_sim = st.button("🔄 Reset Baseline Cascade",    key=f"reset_btn_{sim_key}", use_container_width=True)

        if run_sim:
            # Arm the animation; score resets to baseline so the loop has work to do
            st.session_state[sim_key]                  = baseline
            st.session_state[f"{sim_key}_running"]     = True

        if reset_sim:
            st.session_state[sim_key]                  = baseline
            st.session_state[f"{sim_key}_running"]     = False
            st.rerun()

    # ── Score display slot (updated in-place during animation) ───────
    with col2:
        score_slot = st.empty()

    # ── Animation: step the score down inside a single script run ────
    if st.session_state[f"{sim_key}_running"]:
        N_STEPS  = 40                                   # total animation frames
        drop     = baseline - post_interv
        step_val = drop / N_STEPS if drop > 0 else 0

        current_score = st.session_state[sim_key]
        while current_score > post_interv + step_val * 0.5:
            current_score = max(post_interv, current_score - step_val)
            _render_score_card(score_slot, current_score)
            time.sleep(0.05)

        # Clamp to exact target and mark done
        current_score = post_interv
        st.session_state[sim_key]              = current_score
        st.session_state[f"{sim_key}_running"] = False
        _render_score_card(score_slot, current_score)
    else:
        current_score = st.session_state[sim_key]
        _render_score_card(score_slot, current_score)
    
    # (score card is rendered above inside _render_score_card via score_slot)
        
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
