import json
import streamlit as st
import streamlit.components.v1 as components

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

# ── Per-type Vis.js node appearance ──────────────────────────────────────────
# background: fill color | border: glow ring color | size: radius in px
NODE_STYLES = {
    "mutation": {
        "color": {
            "background": "#FF4B4B",
            "border":     "#FF4B4B",
            "highlight":  {"background": "#FF7070", "border": "#FF4B4B"},
            "hover":      {"background": "#FF6060", "border": "#FF4B4B"},
        },
        "shadow": {"enabled": True, "color": "rgba(255,75,75,0.7)",
                   "size": 16, "x": 0, "y": 0},
        "size": 20,
    },
    "protein": {
        "color": {
            "background": "#FF8E8E",
            "border":     "#FF4B4B",
            "highlight":  {"background": "#FFB0B0", "border": "#FF4B4B"},
            "hover":      {"background": "#FFA0A0", "border": "#FF4B4B"},
        },
        "shadow": {"enabled": True, "color": "rgba(255,75,75,0.4)",
                   "size": 10, "x": 0, "y": 0},
        "size": 16,
    },
    "pathway_node": {
        "color": {
            "background": "#FFAA00",
            "border":     "#FFAA00",
            "highlight":  {"background": "#FFC340", "border": "#FFAA00"},
            "hover":      {"background": "#FFB820", "border": "#FFAA00"},
        },
        "shadow": {"enabled": True, "color": "rgba(255,170,0,0.55)",
                   "size": 14, "x": 0, "y": 0},
        "size": 15,
    },
    "biological_outcome": {
        "color": {
            "background": "#FFAA00",
            "border":     "#FF7043",
            "highlight":  {"background": "#FFC040", "border": "#FF7043"},
            "hover":      {"background": "#FFB030", "border": "#FF7043"},
        },
        "shadow": {"enabled": True, "color": "rgba(255,112,67,0.5)",
                   "size": 12, "x": 0, "y": 0},
        "size": 15,
    },
    "therapeutic": {
        "color": {
            "background": "#00F0FF",
            "border":     "#00F0FF",
            "highlight":  {"background": "#60F8FF", "border": "#00F0FF"},
            "hover":      {"background": "#40F4FF", "border": "#00F0FF"},
        },
        "shadow": {"enabled": True, "color": "rgba(0,240,255,0.7)",
                   "size": 16, "x": 0, "y": 0},
        "size": 18,
    },
}

EDGE_COLORS = {
    "genetic":      "#FFAA00",
    "signaling":    "#FF4B4B",
    "intervention": "#00F0FF",
    "phenotype":    "#888888",
}


def render_network_graph(profile_data):
    """Renders the signaling network as a Vis.js network via st.components.v1.html."""
    graph_data = profile_data.get("graph_data", {})
    raw_nodes  = graph_data.get("nodes", [])
    raw_edges  = graph_data.get("edges", [])

    if not raw_nodes:
        st.warning("No graph data found for this profile.")
        return

    # ── Build Vis.js node / edge arrays ───────────────────────────
    vis_nodes = []
    for n in raw_nodes:
        ntype  = n.get("type", "pathway_node")
        style  = NODE_STYLES.get(ntype, NODE_STYLES["pathway_node"])
        status = n.get("status", "").replace("_", " ").upper()
        mech   = n.get("mechanism", "")
        tip    = mech if mech else (f"Status: {status}" if status else ntype.replace("_", " ").title())

        vis_nodes.append({
            "id":     n["id"],
            "label":  n.get("label", n["id"]),
            "title":  tip,          # tooltip shown on hover
            "color":  style["color"],
            "shadow": style["shadow"],
            "size":   style["size"],
        })

    vis_edges = []
    for idx, e in enumerate(raw_edges):
        etype   = e.get("type", "signaling")
        ec      = EDGE_COLORS.get(etype, "#888888")
        rel     = e.get("relation", "").replace("_", " ")
        vis_edges.append({
            "id":     idx,
            "from":   e.get("source", ""),
            "to":     e.get("target", ""),
            "label":  rel,
            "color":  {"color": ec, "highlight": ec, "hover": ec},
            "arrows": {"to": {"enabled": True, "scaleFactor": 0.8}},
            "font":   {"color": ec, "size": 9,
                       "background": "rgba(14,17,23,0.82)",
                       "strokeWidth": 0},
            "width":  2,
            "smooth": {"type": "curvedCW", "roundness": 0.1},
        })

    nodes_json = json.dumps(vis_nodes)
    edges_json = json.dumps(vis_edges)

    # ── Vis.js options ────────────────────────────────────────────
    options = {
        "physics": {
            "stabilization": True,
            "barnesHut": {
                "gravitationalConstant": -2000,
                "centralGravity":        0.3,
                "springLength":          95,
            },
        },
        "nodes": {
            "shape":       "dot",
            "font":        {"color": "#FFFFFF", "size": 14, "face": "sans-serif"},
            "borderWidth": 2,
            "shadow":      True,
        },
        "edges": {
            "width":          2,
            "selectionWidth": 3,
            "smooth":         {"type": "curvedCW", "roundness": 0.1},
        },
        "interaction": {
            "hover":         True,
            "tooltipDelay":  120,
            "navigationButtons": False,
            "keyboard":      False,
        },
        "layout": {
            "improvedLayout": True,
        },
    }
    options_json = json.dumps(options)

    # ── HTML / JS template ────────────────────────────────────────
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: transparent;
      font-family: 'Outfit', 'Inter', sans-serif;
    }}
    #header {{
      padding: 10px 4px 6px;
    }}
    #header h3 {{
      font-size: 1.25rem;
      font-weight: 600;
      color: #FFFFFF;
      margin-bottom: 3px;
    }}
    #header p {{
      font-size: 0.82rem;
      color: #A0A0A0;
    }}
    #network-container {{
      width: 100%;
      height: 460px;
      background: rgba(22,27,34,0.60);
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 10px;
      overflow: hidden;
    }}
    /* Legend pill row */
    #legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 8px 4px 0;
    }}
    .leg-item {{
      display: flex;
      align-items: center;
      gap: 5px;
      font-size: 0.75rem;
      color: #C9D1D9;
    }}
    .leg-dot {{
      width: 12px; height: 12px;
      border-radius: 50%;
      flex-shrink: 0;
    }}
  </style>
  <!-- Vis.js Network CDN -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
  <link  rel="stylesheet"
         href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css" />
</head>
<body>
  <div id="header">
    <h3>Biological Signaling Network</h3>
    <p>Interactive cascade map — mutated drivers, downstream nodes, and targeted inhibitors</p>
  </div>
  <div id="network-container"></div>
  <div id="legend">
    <div class="leg-item">
      <div class="leg-dot" style="background:#FF4B4B;box-shadow:0 0 6px #FF4B4B;"></div>
      Mutation
    </div>
    <div class="leg-item">
      <div class="leg-dot" style="background:#FF8E8E;box-shadow:0 0 4px #FF4B4B;"></div>
      Protein
    </div>
    <div class="leg-item">
      <div class="leg-dot" style="background:#FFAA00;box-shadow:0 0 6px #FFAA00;"></div>
      Pathway / Outcome
    </div>
    <div class="leg-item">
      <div class="leg-dot" style="background:#00F0FF;box-shadow:0 0 6px #00F0FF;"></div>
      Therapeutic
    </div>
  </div>

  <script>
    const nodes   = new vis.DataSet({nodes_json});
    const edges   = new vis.DataSet({edges_json});
    const options = {options_json};

    const container = document.getElementById('network-container');
    const network   = new vis.Network(container, {{ nodes, edges }}, options);

    // Dim stabilisation spinner when physics settles
    network.on('stabilizationIterationsDone', function () {{
      network.setOptions({{ physics: {{ enabled: false }} }});
    }});
  </script>
</body>
</html>
"""

    components.html(html, height=580, scrolling=False)
