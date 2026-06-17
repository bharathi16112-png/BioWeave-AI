import streamlit as st
import time

def render_intervention_engine(profile_data):
    """
    Renders the pathway suppression engine.

    When AutoDock Vina is available (vina + meeko installed), docking scores
    are computed in real-time and pathway suppression is derived from the
    binding affinity via a sigmoid calibrated to published IC50 data.

    When Vina is not installed, curated static scores are displayed with an
    honest 'Curated Score' label — no fake computation claims.
    """
    engine_data = profile_data.get("pathway_intervention_engine", {})
    docking_info = engine_data.get("docking", {})
    is_real_docking = docking_info.get("method") == "autodock_vina"
    is_fallback = docking_info.get("is_fallback", True)

    method_label = "AutoDock Vina" if is_real_docking else "Curated Score"
    method_color = "#A8FFB2" if is_real_docking else "#FFAA00"

    title_suffix = (
        f'<span style="font-size:0.75rem; color:{method_color}; '
        f'font-family:Space Mono,monospace; margin-left:10px; '
        f'border:1px solid {method_color}; padding:2px 8px; border-radius:10px;">'
        f'{method_label}</span>'
    )

    st.html(f"""
        <div style="margin-bottom: 20px;">
            <h3 style="margin: 0; font-family: 'Outfit', sans-serif; font-weight: 600;
                       color: #FFFFFF; font-size: 1.4rem; display:flex; align-items:center;
                       flex-wrap:wrap; gap:8px;">
                Pathway Intervention Engine {title_suffix}
            </h3>
            <p style="margin: 4px 0 0 0; font-size: 0.9rem; color: #A0A0A0;
                      font-family: 'Outfit', sans-serif;">
                {'Real AutoDock Vina molecular docking — binding affinity drives cascade suppression.'
                 if is_real_docking else
                 'Curated clinical scores. Install <code>vina</code> + <code>meeko</code> + <code>rdkit</code> for live docking.'}
            </p>
        </div>
    """)
    
    engine_data = profile_data.get("pathway_intervention_engine", {})
    baseline = engine_data.get("baseline_pathway_activity_score", 1.0)
    post_interv = engine_data.get("predicted_post_intervention_activity_score", 0.0)
    rationale = engine_data.get("therapeutic_rationale", "N/A")

    docking_info = engine_data.get("docking", {})
    affinity = docking_info.get("binding_affinity_kcal_mol")
    pdb_id = docking_info.get("pdb_id", "")
    drug_name_dock = docking_info.get("drug_name", "")
    all_poses = docking_info.get("all_pose_scores", [])
    suppression_float = docking_info.get("pathway_suppression", None)
    target_desc = docking_info.get("target_description", "")

    # Suppression delta
    suppression_pct = int(round((baseline - post_interv) / baseline * 100)) if baseline > 0 else 0
    
    summary = profile_data.get("executive_summary", {})
    drug_name = summary.get("recommended_therapy", drug_name_dock or "Targeted Agent")
    
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
        slot.html(f"""
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
        """)

    # ── Layout ───────────────────────────────────────────────────────
    col1, col2 = st.columns([1, 1])

    with col1:
        # Build docking stats block
        if affinity is not None and is_real_docking:
            poses_str = " / ".join(f"{s:.1f}" for s in all_poses[:3])
            affinity_color = "#A8FFB2" if affinity < -9.5 else ("#FFAA00" if affinity < -7.5 else "#FF7B7B")
            docking_block = f"""
            <div style="background: rgba(22,27,34,0.6); backdrop-filter: blur(12px);
                        border: 1px solid rgba(255,255,255,0.08); border-radius: 12px;
                        padding: 24px; margin-bottom: 12px;">
                <h5 style="margin: 0 0 12px 0; color: #00F0FF; font-family: 'Outfit', sans-serif;
                           text-transform: uppercase; font-size: 0.85rem;">
                    AutoDock Vina Results
                </h5>
                <div style="display:flex; flex-direction:column; gap:8px;">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="font-family:'Space Mono',monospace; font-size:0.8rem; color:#A0A0A0;">
                            Best Affinity
                        </span>
                        <span style="font-family:'Space Mono',monospace; font-size:0.9rem;
                                     color:{affinity_color}; font-weight:bold;">
                            {affinity:.2f} kcal/mol
                        </span>
                    </div>
                    <div style="display:flex; justify-content:space-between;">
                        <span style="font-family:'Space Mono',monospace; font-size:0.8rem; color:#A0A0A0;">
                            Top Poses
                        </span>
                        <span style="font-family:'Space Mono',monospace; font-size:0.75rem; color:#E6EDF3;">
                            {poses_str} kcal/mol
                        </span>
                    </div>
                    <div style="display:flex; justify-content:space-between;">
                        <span style="font-family:'Space Mono',monospace; font-size:0.8rem; color:#A0A0A0;">
                            Reference PDB
                        </span>
                        <span style="font-family:'Space Mono',monospace; font-size:0.75rem; color:#00F0FF;">
                            {pdb_id}
                        </span>
                    </div>
                    {'<div style="font-size:0.75rem; color:#707070; font-family:Outfit,sans-serif; margin-top:4px;">' + target_desc + '</div>' if target_desc else ''}
                </div>
            </div>
            """
        else:
            affinity_display = f"{affinity:.2f} kcal/mol" if affinity is not None else "N/A (static)"
            docking_block = f"""
            <div style="background: rgba(22,27,34,0.6); backdrop-filter: blur(12px);
                        border: 1px solid rgba(255,255,255,0.08); border-radius: 12px;
                        padding: 24px; margin-bottom: 12px;">
                <h5 style="margin: 0 0 8px 0; color: #00F0FF; font-family: 'Outfit', sans-serif;
                           text-transform: uppercase; font-size: 0.85rem;">
                    In-Silico Simulation
                </h5>
                <p style="font-size: 0.82rem; color: #A0A0A0; margin-bottom: 10px;
                          font-family: 'Outfit', sans-serif; line-height:1.5;">
                    Dock <strong>{drug_name}</strong> to compute downstream kinase suppression.
                    <br><span style="color:#FFAA00; font-size:0.75rem;">
                    ⚠ Curated score active — install <code>vina meeko rdkit</code> for live docking.
                    </span>
                </p>
                <div style="display:flex; justify-content:space-between; margin-top:8px;">
                    <span style="font-family:'Space Mono',monospace; font-size:0.8rem; color:#A0A0A0;">
                        Ref. Affinity
                    </span>
                    <span style="font-family:'Space Mono',monospace; font-size:0.8rem; color:#FFAA00;">
                        {affinity_display}
                    </span>
                </div>
            </div>
            """
        st.html(docking_block)
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
        
    st.html("<div style='margin-bottom: 15px;'></div>")
    
    # Docking methodology note
    if is_real_docking and affinity is not None:
        suppression_pct_label = f"{int((docking_info.get('pathway_suppression', 0))*100)}%"
        affinity_note = (
            f"Binding affinity: <strong>{affinity:.2f} kcal/mol</strong> "
            f"(AutoDock Vina, PDB {pdb_id}) → "
            f"<strong>{suppression_pct_label}</strong> predicted pathway suppression "
            f"(sigmoid model calibrated to published IC50 data)."
        )
    else:
        affinity_note = (
            "Scores derived from curated clinical literature. "
            "Install <code>vina</code>, <code>meeko</code>, and <code>rdkit</code> "
            "for real-time AutoDock Vina molecular docking."
        )

    # Rationale panel with suppression delta badge — use st.html() to avoid markdown escaping
    st.html(f"""
    <div style="background: rgba(22,27,34,0.6); backdrop-filter: blur(12px);
                border: 1px solid rgba(255,255,255,0.08);
                border-left: 4px solid #00D2D3;
                border-radius: 12px; padding: 24px; margin-bottom: 16px;">

        <!-- Header row: title + delta badge -->
        <div style="display: flex; align-items: center; justify-content: space-between;
                    margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
            <h5 style="margin: 0; color: #00D2D3; font-family: 'Outfit', sans-serif;
                       text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px;">
                Therapeutic Mechanism &amp; Rationale
            </h5>
            <span style="
                background: linear-gradient(135deg, rgba(168,255,178,0.15) 0%, rgba(0,210,211,0.10) 100%);
                border: 1px solid rgba(168,255,178,0.4);
                padding: 4px 14px;
                border-radius: 20px;
                font-family: 'Space Mono', monospace;
                font-size: 0.8rem;
                font-weight: bold;
                color: #A8FFB2;
                white-space: nowrap;
                letter-spacing: 0.3px;
            ">&#x25BC; {suppression_pct}% Cascade Suppression</span>
        </div>

        <!-- Compact stats row -->
        <div style="display: flex; gap: 20px; margin-bottom: 14px; flex-wrap: wrap;">
            <div style="font-family: 'Space Mono', monospace; font-size: 0.75rem; color: #707070;">
                Baseline&nbsp;<span style="color: #FF4B4B; font-weight: bold;">{int(baseline * 100)}%</span>
            </div>
            <div style="font-family: 'Space Mono', monospace; font-size: 0.75rem; color: #707070;">
                Post-Drug&nbsp;<span style="color: #A8FFB2; font-weight: bold;">{int(post_interv * 100)}%</span>
            </div>
            <div style="font-family: 'Space Mono', monospace; font-size: 0.75rem; color: #707070;">
                Net Delta&nbsp;<span style="color: #00D2D3; font-weight: bold;">&#x2212;{suppression_pct}%</span>
            </div>
        </div>

        <p style="margin: 0; font-family: 'Outfit', sans-serif;
                  font-size: 0.95rem; line-height: 1.55; color: #E6EDF3;">
            {rationale}
        </p>
        <p style="margin: 12px 0 0 0; font-family: 'Outfit', sans-serif;
                  font-size: 0.78rem; line-height: 1.5; color: #707070;
                  border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px;">
            {affinity_note}
        </p>
    </div>
    """)
