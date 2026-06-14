import math
import streamlit as st
import plotly.graph_objects as go

# Fixed layout positions for a clean left-to-right signaling cascade
# Keys match node IDs in the JSON; fallback spreads unknowns in a circle
LAYOUT_HINTS = {
    "N1": (0.0,  0.0),   # BRAF V600E (mutation driver)
    "N2": (2.0,  0.0),   # B-Raf Kinase Monomer (protein)
    "N3": (4.0,  0.0),   # MEK 1/2 (pathway)
    "N4": (6.0,  0.0),   # ERK 1/2 (pathway)
    "N5": (8.0,  0.0),   # Cell Proliferation (outcome)
    "N6": (2.0,  2.5),   # Dabrafenib (therapeutic → targets N2)
    "N7": (4.0,  2.5),   # Trametinib  (therapeutic → targets N3)
}

NODE_COLORS = {
    "mutation":          "#FF4B4B",
    "protein":           "#FF8E8E",
    "pathway_node":      "#FFAF66",
    "biological_outcome":"#FF7043",
    "therapeutic":       "#00D2D3",
}

EDGE_COLORS = {
    "genetic":      "#FFAF66",
    "signaling":    "#FF4B4B",
    "intervention": "#00D2D3",
    "phenotype":    "#888888",
}

NODE_SIZES = {
    "mutation": 28,
    "protein":  22,
    "pathway_node": 20,
    "biological_outcome": 20,
    "therapeutic": 24,
}

NODE_SYMBOLS = {
    "mutation": "circle",
    "protein":  "circle",
    "pathway_node": "circle",
    "biological_outcome": "diamond",
    "therapeutic": "square",
}


def _auto_layout(nodes):
    """Assign positions: use hints for known IDs, distribute rest in a circle."""
    positions = {}
    unknown = []
    for n in nodes:
        nid = n["id"]
        if nid in LAYOUT_HINTS:
            positions[nid] = LAYOUT_HINTS[nid]
        else:
            unknown.append(nid)
    r = 3.0
    for i, nid in enumerate(unknown):
        angle = 2 * math.pi * i / max(len(unknown), 1)
        positions[nid] = (r * math.cos(angle), r * math.sin(angle) + 3.0)
    return positions


def render_network_graph(profile_data):
    """Renders the signaling network as a Plotly graph — no external JS needed."""
    graph_data = profile_data.get("graph_data", {})
    nodes      = graph_data.get("nodes", [])
    edges      = graph_data.get("edges", [])

    st.html("""
    <div style="margin-bottom: 14px; font-family: 'Outfit', sans-serif;">
        <h3 style="margin: 0; font-weight: 600; color: #FFFFFF; font-size: 1.4rem;">
            Biological Signaling Network
        </h3>
        <p style="margin: 4px 0 0 0; font-size: 0.9rem; color: #A0A0A0;">
            Interactive cascade map — mutated drivers, downstream nodes, and targeted inhibitors
        </p>
    </div>
    """)

    if not nodes:
        st.warning("No graph data found for this profile.")
        return

    pos = _auto_layout(nodes)

    # Build a lookup: id → node dict
    node_map = {n["id"]: n for n in nodes}

    # ── Edge traces ───────────────────────────────────────────────
    edge_traces = []
    annotation_list = []

    for e in edges:
        src_id   = e.get("source", "")
        tgt_id   = e.get("target", "")
        etype    = e.get("type", "signaling")
        relation = e.get("relation", "").replace("_", " ")
        conf     = e.get("confidence", 1.0)

        if src_id not in pos or tgt_id not in pos:
            continue

        x0, y0 = pos[src_id]
        x1, y1 = pos[tgt_id]
        color   = EDGE_COLORS.get(etype, "#888888")

        # Draw edge line
        edge_traces.append(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode="lines",
            line=dict(width=2.2, color=color),
            hoverinfo="none",
            showlegend=False,
        ))

        # Midpoint annotation for relation label — dark pill background
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        # Offset edge labels perpendicular to the line slightly
        is_vertical = abs(x1 - x0) < 0.5
        label_xshift = 18 if is_vertical else 0
        label_yshift = 0  if is_vertical else 14
        annotation_list.append(dict(
            x=mx, y=my,
            text=f"<b>{relation}</b>",
            showarrow=False,
            font=dict(size=9, color="#FFFFFF", family="Space Mono, monospace"),
            bgcolor=color,
            bordercolor=color,
            borderwidth=1,
            borderpad=3,
            opacity=0.9,
            xshift=label_xshift,
            yshift=label_yshift,
        ))

        # Arrowhead annotation pointing toward target
        annotation_list.append(dict(
            x=x1, y=y1,
            ax=x0, ay=y0,
            xref="x", yref="y",
            axref="x", ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.2,
            arrowwidth=2,
            arrowcolor=color,
        ))

    # Nodes that sit on the y=0 cascade line — alternate labels above / below
    # so they never overlap each other or the connecting lines.
    node_x, node_y, node_hover = [], [], []
    node_colors, node_sizes, node_symbols = [], [], []

    LABEL_SIDE = {
        "N1": "below",   # BRAF V600E
        "N2": "above",   # B-Raf Kinase
        "N3": "below",   # MEK
        "N4": "above",   # ERK
        "N5": "below",   # Cell Proliferation
        "N6": "above",   # Dabrafenib (already above cascade line)
        "N7": "above",   # Trametinib
    }


    for n in nodes:
        nid      = n["id"]
        if nid not in pos:
            continue
        x, y     = pos[nid]
        ntype    = n.get("type", "pathway_node")
        label    = n.get("label", nid)
        status   = n.get("status", "").replace("_", " ").upper()
        mechanism= n.get("mechanism", "")

        node_x.append(x)
        node_y.append(y)
        hover_extra = mechanism if mechanism else (f"Status: {status}" if status else "")
        node_hover.append(
            f"<b>{label}</b><br>Type: {ntype.replace('_',' ').title()}"
            + (f"<br>{hover_extra}" if hover_extra else "")
        )
        node_colors.append(NODE_COLORS.get(ntype, "#888888"))
        node_sizes.append(NODE_SIZES.get(ntype, 20))
        node_symbols.append(NODE_SYMBOLS.get(ntype, "circle"))

        # Add node label as a separate annotation with a dark pill background
        side   = LABEL_SIDE.get(nid, "below")
        yshift = -28 if side == "below" else 28
        annotation_list.append(dict(
            x=x, y=y,
            text=f"<b>{label}</b>",
            showarrow=False,
            font=dict(size=10.5, color="#E6EDF3", family="Outfit, Arial"),
            bgcolor="rgba(14,17,23,0.88)",
            bordercolor="rgba(255,255,255,0.12)",
            borderwidth=1,
            borderpad=4,
            yshift=yshift,
        ))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",          # markers ONLY — labels handled by annotations
        marker=dict(
            symbol=node_symbols,
            size=node_sizes,
            color=node_colors,
            line=dict(width=2, color="rgba(255,255,255,0.3)"),
        ),
        hovertext=node_hover,
        hoverinfo="text",
        hoverlabel=dict(
            bgcolor="rgba(22,27,34,0.95)",
            bordercolor="rgba(255,255,255,0.2)",
            font=dict(size=12, color="#E6EDF3", family="Outfit, Arial"),
        ),
        showlegend=False,
    )

    # ── Legend traces (invisible, just for the legend box) ────────
    legend_items = [
        ("Mutation / Protein",  "#FF4B4B",  "circle"),
        ("Pathway / Outcome",   "#FFAF66",  "circle"),
        ("Therapeutic Agent",   "#00D2D3",  "square"),
        ("Signaling Edge",      "#FF4B4B",  None),
        ("Intervention Edge",   "#00D2D3",  None),
    ]
    legend_traces = []
    for name, color, symbol in legend_items:
        if symbol:
            legend_traces.append(go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=10, color=color, symbol=symbol),
                name=name,
                showlegend=True,
            ))
        else:
            legend_traces.append(go.Scatter(
                x=[None], y=[None],
                mode="lines",
                line=dict(width=3, color=color),
                name=name,
                showlegend=True,
            ))

    # ── Assemble figure ───────────────────────────────────────────
    fig = go.Figure(
        data=edge_traces + [node_trace] + legend_traces,
        layout=go.Layout(
            paper_bgcolor="rgba(14,17,23,0)",
            plot_bgcolor="rgba(22,27,34,0.6)",
            height=500,
            margin=dict(l=30, r=160, t=30, b=30),
            xaxis=dict(
                showgrid=False, zeroline=False,
                showticklabels=False,
                range=[-0.8, 9.2],
            ),
            yaxis=dict(
                showgrid=False, zeroline=False,
                showticklabels=False,
                range=[-1.0, 3.8],
            ),
            legend=dict(
                bgcolor="rgba(22,27,34,0.85)",
                bordercolor="rgba(255,255,255,0.1)",
                borderwidth=1,
                font=dict(size=11, color="#C9D1D9", family="Outfit, Arial"),
                x=1.0, y=1.0,
                xanchor="right",
                yanchor="top",
            ),
            annotations=annotation_list,
            hoverdistance=15,
        )
    )

    st.plotly_chart(fig, width="stretch", config={
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["autoScale2d", "lasso2d", "select2d"],
        "displaylogo": False,
    })
