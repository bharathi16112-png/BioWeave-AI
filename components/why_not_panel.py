import streamlit as st

# Shared card style (fully inline, no CSS classes)
CARD = (
    "background: rgba(22,27,34,0.6);"
    "backdrop-filter: blur(12px);"
    "border: 1px solid rgba(255,255,255,0.08);"
    "border-radius: 12px;"
    "padding: 20px 22px;"
    "margin-bottom: 12px;"
    "font-family: 'Outfit', sans-serif;"
)

def render_why_not_panel(profile_data):
    """Renders the why-not exclusion panel using st.html() to avoid markdown sanitization."""
    exclusions = profile_data.get("why_not_exclusion_panel", [])

    header = """
    <div style="margin-bottom: 18px; font-family: 'Outfit', sans-serif;">
        <h3 style="margin: 0; font-weight: 600; color: #FFFFFF; font-size: 1.4rem;">
            Clinical Contraindications &amp; Exclusions
        </h3>
        <p style="margin: 4px 0 0 0; font-size: 0.9rem; color: #A0A0A0;">
            Counterfactual reasoning explaining why alternative therapeutic interventions were discarded
        </p>
    </div>
    """
    st.html(header)

    if not exclusions:
        st.info("No exclusions specified for this profile.")
        return

    for item in exclusions:
        drug       = item.get("drug_name", "Alternative Agent")
        drug_class = item.get("class", "N/A")
        status     = item.get("status", "Excluded")
        reasoning  = item.get("reasoning", "N/A")

        card_html = f"""
        <div style="{CARD} border-left: 4px solid #FF4B4B;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                <span style="font-weight: bold; color: #FF4B4B; font-size: 1.05rem; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.2rem;">&#9888;&#65039;</span> {drug}
                </span>
                <span style="
                    background-color: rgba(255,75,75,0.1);
                    border: 1px solid rgba(255,75,75,0.3);
                    padding: 2px 10px;
                    border-radius: 4px;
                    font-family: 'Space Mono', monospace;
                    font-size: 0.7rem;
                    color: #FF4B4B;
                    font-weight: bold;
                    text-transform: uppercase;
                    white-space: nowrap;
                ">{status}</span>
            </div>
            <div style="font-family: 'Space Mono', monospace; font-size: 0.8rem; color: #FFAF66; margin-bottom: 8px;">
                Class: {drug_class}
            </div>
            <div style="font-size: 0.92rem; line-height: 1.55; color: #E6EDF3;">
                {reasoning}
            </div>
        </div>
        """
        st.html(card_html)
