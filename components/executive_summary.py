import streamlit as st

def render_executive_summary(profile_data):
    """Renders the executive summary card using st.html() to avoid markdown HTML sanitization."""
    summary   = profile_data.get("executive_summary", {})
    metadata  = profile_data.get("metadata", {})
    metrics   = profile_data.get("system_metrics", {})

    mutation            = summary.get("mutation", "N/A")
    clinical_signif     = summary.get("clinical_significance", "N/A")
    affected_pathway    = summary.get("affected_pathway", "N/A")
    recommended_therapy = summary.get("recommended_therapy", "N/A")
    confidence          = summary.get("confidence", 0.0)
    confidence_pct      = int(confidence * 100)

    patient_id  = metadata.get("patient_id", "N/A")
    tumor_type  = metadata.get("primary_tumor_type", "N/A")
    mut_details = metadata.get("mutation", {})
    gene        = mut_details.get("gene", "N/A")
    variant     = mut_details.get("variant", "N/A")
    family      = mut_details.get("family", "N/A")

    gpu     = metrics.get("gpu_hardware", "N/A")
    compute = metrics.get("compute_platform", "N/A")
    latency = metrics.get("total_latency_ms", 0)
    tokens  = metrics.get("tokens_generated", 0)
    vram    = metrics.get("vram_allocated_gb", 0.0)

    signif_color = "#FF4B4B" if clinical_signif.lower() == "pathogenic" else "#FFAF66"
    signif_bg    = "rgba(255,75,75,0.1)"
    signif_bd    = "rgba(255,75,75,0.3)"

    html = f"""
    <div style="font-family: 'Outfit', sans-serif;">

      <!-- ═══ TELEMETRY BANNER ═══ -->
      <div style="
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(135deg, rgba(237,20,91,0.05) 0%, rgba(22,27,34,0.8) 100%);
        border-left: 4px solid #ED145B;
        border-radius: 6px;
        padding: 14px 20px;
        margin: 0 0 20px 0;
        flex-wrap: wrap;
        gap: 10px;
      ">
        <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
          <span style="
            background-color: rgba(237,20,91,0.15);
            color: #ED145B;
            border: 1px solid rgba(237,20,91,0.3);
            padding: 4px 10px;
            border-radius: 12px;
            font-family: 'Space Mono', monospace;
            font-size: 0.82rem;
            font-weight: bold;
          ">ROCm ENGINE ACTIVE</span>
          <span style="font-weight: 600; color: #FFFFFF; font-size: 0.95rem;">
            {gpu} &bull; <span style="color: #ED145B;">{compute}</span>
          </span>
          <span style="color: rgba(255,255,255,0.2);">|</span>
          <span style="font-family: 'Space Mono', monospace; font-size: 0.83rem; color: #A0A0A0;">
            VRAM: <span style="color: #00D2D3; font-weight: bold;">{vram} GB</span>
          </span>
          <span style="color: rgba(255,255,255,0.2);">|</span>
          <span style="font-family: 'Space Mono', monospace; font-size: 0.83rem; color: #A0A0A0;">
            Tokens: <span style="color: #FFAF66; font-weight: bold;">{tokens}</span>
          </span>
        </div>
        <div style="font-family: 'Space Mono', monospace; font-size: 0.88rem; color: #E0E6ED;">
          Latency: <span style="color: #00D2D3; font-weight: bold;">{latency} ms</span>
        </div>
      </div>

      <!-- ═══ MAIN CARDS ROW ═══ -->
      <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 16px; align-items: stretch;">

        <!-- LEFT: Diagnostic Profile Card -->
        <div style="
          background: rgba(22,27,34,0.6);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 12px;
          padding: 24px;
          transition: border-color 0.3s ease;
        ">
          <!-- Card header -->
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
            <div>
              <h4 style="
                margin: 0;
                color: #00D2D3;
                font-size: 0.95rem;
                font-weight: 600;
                letter-spacing: 0.5px;
                text-transform: uppercase;
              ">Diagnostic Target Profile</h4>
              <div style="
                font-size: 2.2rem;
                font-weight: 800;
                letter-spacing: -0.8px;
                background: linear-gradient(90deg, #FFFFFF 0%, #A0A0A0 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 5px 0 0 0;
                line-height: 1.1;
              ">{mutation}</div>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 0.75rem; color: #A0A0A0; text-transform: uppercase; letter-spacing: 0.5px;">Patient ID</div>
              <div style="font-size: 1rem; font-weight: bold; color: #FFFFFF; font-family: 'Space Mono', monospace;">{patient_id}</div>
            </div>
          </div>

          <!-- Metadata grid -->
          <div style="
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            border-top: 1px solid rgba(255,255,255,0.06);
            padding-top: 15px;
            margin-top: 10px;
          ">
            <div>
              <span style="color: #A0A0A0; font-size: 0.78rem; display: block; margin-bottom: 3px; text-transform: uppercase; letter-spacing: 0.4px;">Primary Tumor Type</span>
              <strong style="color: #FFFFFF; font-size: 0.92rem;">{tumor_type}</strong>
            </div>
            <div>
              <span style="color: #A0A0A0; font-size: 0.78rem; display: block; margin-bottom: 3px; text-transform: uppercase; letter-spacing: 0.4px;">Biomarker Cascade</span>
              <strong style="color: #FFAF66; font-size: 0.92rem;">{gene} ({variant}) &bull; {family} Family</strong>
            </div>
          </div>

          <!-- Therapy recommendation -->
          <div style="border-top: 1px solid rgba(255,255,255,0.06); padding-top: 15px; margin-top: 15px;">
            <span style="color: #A0A0A0; font-size: 0.78rem; display: block; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.4px;">Recommended Therapeutic Strategy</span>
            <strong style="color: #A8FFB2; font-size: 1.15rem; font-weight: 600;">{recommended_therapy}</strong>
          </div>
        </div>

        <!-- RIGHT: Confidence + Clinical Significance Card -->
        <div style="
          background: rgba(22,27,34,0.6);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 12px;
          padding: 24px;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          text-align: center;
          gap: 4px;
        ">
          <h4 style="margin: 0 0 8px 0; color: #A0A0A0; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
            Clinical Interpretation
          </h4>

          <!-- Significance badge -->
          <div style="
            background-color: {signif_bg};
            border: 1px solid {signif_bd};
            padding: 4px 14px;
            border-radius: 6px;
            font-family: 'Space Mono', monospace;
            font-size: 0.88rem;
            color: {signif_color};
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 18px;
          ">{clinical_signif}</div>

          <!-- Confidence score -->
          <h4 style="margin: 0 0 4px 0; color: #A0A0A0; font-size: 0.82rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
            Consensus Confidence
          </h4>
          <div style="font-size: 3.2rem; font-weight: 800; color: #00D2D3; line-height: 1.1; margin: 4px 0;">
            {confidence_pct}%
          </div>

          <!-- Progress bar -->
          <div style="width: 100%; background-color: rgba(255,255,255,0.08); border-radius: 10px; height: 6px; overflow: hidden; margin: 8px 0 6px 0;">
            <div style="width: {confidence_pct}%; background: linear-gradient(90deg, #00D2D3 0%, #008283 100%); height: 100%; border-radius: 10px;"></div>
          </div>

          <span style="color: #606060; font-size: 0.7rem; font-family: 'Space Mono', monospace; text-transform: uppercase; letter-spacing: 0.3px;">
            Multi-Agent Validation Consensus
          </span>
        </div>

      </div>
    </div>
    """

    st.html(html)
