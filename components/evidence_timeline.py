import streamlit as st

CARD = (
    "background: rgba(22,27,34,0.6);"
    "backdrop-filter: blur(12px);"
    "border: 1px solid rgba(255,255,255,0.08);"
    "border-radius: 12px;"
    "padding: 18px 22px;"
    "margin-bottom: 12px;"
    "font-family: 'Outfit', sans-serif;"
)

def render_evidence_timeline(profile_data):
    """Renders the evidence citations using st.html() to avoid markdown sanitization."""
    timeline = profile_data.get("evidence_timeline", [])

    header = """
    <div style="margin-bottom: 18px; font-family: 'Outfit', sans-serif;">
        <h3 style="margin: 0; font-weight: 600; color: #FFFFFF; font-size: 1.4rem;">
            Scientific Evidence &amp; Provenance
        </h3>
        <p style="margin: 4px 0 0 0; font-size: 0.9rem; color: #A0A0A0;">
            Verified genomic resources, pathway mappings, and regulatory documentation
        </p>
    </div>
    """
    st.html(header)

    if not timeline:
        st.info("No evidence citations found.")
        return

    for item in timeline:
        step        = item.get("step", 1)
        source      = item.get("source_name", "NCBI")
        url         = item.get("url", "#")
        assertion   = item.get("assertion", "Clinical Citation")
        evidence_id = item.get("evidence_id", "N/A")
        confidence  = item.get("confidence_score", 1.0)
        snippet     = item.get("snippet", "N/A")
        conf_pct    = int(confidence * 100)

        # Color code by source database
        src_lower = source.lower()
        if "clinvar" in src_lower:
            badge_bg, text_col, badge_bd = "rgba(46,204,113,0.15)", "#2ecc71", "rgba(46,204,113,0.3)"
        elif "kegg" in src_lower:
            badge_bg, text_col, badge_bd = "rgba(230,126,34,0.15)", "#e67e22", "rgba(230,126,34,0.3)"
        elif "fda" in src_lower or "oncokb" in src_lower:
            badge_bg, text_col, badge_bd = "rgba(52,152,219,0.15)", "#3498db", "rgba(52,152,219,0.3)"
        else:
            badge_bg, text_col, badge_bd = "rgba(155,89,182,0.15)", "#9b59b6", "rgba(155,89,182,0.3)"

        card_html = f"""
        <div style="{CARD}">
            <!-- Header row: badges + link -->
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="
                        background-color: rgba(255,255,255,0.05);
                        border: 1px solid rgba(255,255,255,0.15);
                        padding: 1px 7px;
                        border-radius: 4px;
                        font-family: 'Space Mono', monospace;
                        font-size: 0.68rem;
                        color: #FFFFFF;
                        font-weight: bold;
                    ">STEP {step}</span>
                    <span style="
                        background-color: {badge_bg};
                        border: 1px solid {badge_bd};
                        padding: 1px 9px;
                        border-radius: 4px;
                        font-family: 'Space Mono', monospace;
                        font-size: 0.72rem;
                        color: {text_col};
                        font-weight: bold;
                    ">{source.upper()}</span>
                </div>
                <a href="{url}" target="_blank" style="
                    text-decoration: none;
                    color: #00D2D3;
                    font-size: 0.85rem;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 3px;
                ">Open Source Registry <span style="font-size: 0.95rem;">&#8599;</span></a>
            </div>

            <!-- Assertion title -->
            <h5 style="margin: 0 0 6px 0; font-weight: 600; color: #FFFFFF; font-size: 0.98rem;">
                {assertion}&nbsp;
                <span style="color: #707070; font-size: 0.78rem; font-family: 'Space Mono', monospace; font-weight: normal;">(ID: {evidence_id})</span>
            </h5>

            <!-- Snippet -->
            <p style="margin: 0 0 10px 0; font-size: 0.9rem; line-height: 1.5; color: #A0A0A0;">
                {snippet}
            </p>

            <!-- Confidence -->
            <div style="font-family: 'Space Mono', monospace; font-size: 0.75rem; color: #707070;">
                Curation Confidence: <span style="color: #00D2D3; font-weight: bold;">{conf_pct}%</span>
            </div>
        </div>
        """
        st.html(card_html)
