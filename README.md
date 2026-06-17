# 🧬 BioWeave-AI: Multi-Agent Precision Oncology Engine

BioWeave-AI is a high-performance, multi-agent reasoning platform designed for real-time clinical genomic analysis. Built natively for the **AMD Instinct™ MI300X** acceleration platform utilizing the **ROCm™ v6.x** compute stack, it ingests unstructured clinical oncology reports and structurally maps them to actionable therapeutic interventions, dynamic signaling networks, and literature-backed evidence.

## ✨ Core Capabilities

- **Live Local Inference:** Leverages a locally hosted `Meta-Llama-3-8B-Instruct` model loaded directly into MI300X VRAM via native PyTorch ROCm/HIP compatibility. 
- **Multi-Agent Orchestration:**
  - 🕵️ **Molecular Detective:** Extracts complex variant signatures (e.g., BRAF V600E) and determines clinical significance.
  - 🕸️ **Pathway Pathologist:** Maps biological signaling cascades using interactive, physics-driven Vis.js network graphs.
  - 💊 **Therapeutic Matchmaker:** Simulates downstream kinase suppression in real-time and filters out clinical contraindications.
- **Premium Glassmorphism UI:** A sleek, medical-telemetry-inspired Streamlit interface featuring dynamic animations and custom CSS overlays.

## ⚡ AMD Instinct Acceleration Benchmarks

- **Hardware:** AMD Instinct MI300X (192GB HBM3 VRAM)
- **Software Stack:** Native PyTorch with ROCm/HIP compilation
- **Performance:** Full 8B parameter model mapped to `cuda:0` achieving sub-second multi-agent trace parsing and structural JSON extraction.

## 🧩 Project Structure

```text
├── app.py                      # Main Streamlit dashboard entrypoint
├── pipeline.py                 # MI300X Llama-3 inference & schema extraction logic
├── requirements.txt            # Python dependencies (Streamlit, Torch, Transformers, etc.)
├── assets/
│   └── style.css               # Premium telemetry glassmorphism styling
├── components/
│   ├── agent_trace.py          # Displays the multi-agent reasoning steps
│   ├── evidence_timeline.py    # Chronological registry of trial/approval evidence
│   ├── executive_summary.py    # High-level KPI and diagnostic overview
│   ├── intervention_engine.py  # Real-time animated pathway suppression simulation
│   ├── network_graph.py        # Vis.js physics-based biological network renderer
│   └── why_not_panel.py        # Clinical contraindications and exclusions
└── utils/
    └── data_loader.py          # Profile management and mock data fallback
```

## 🛠️ Installation & Local Startup

**Prerequisites:** An environment with ROCm and compatible PyTorch installed.

```bash
# Clone the repository
git clone https://github.com/bharathi16112-png/BioWeave-AI.git
cd BioWeave-AI

# Activate your AMD cluster virtual environment
source /workspace/shared/bio_env/bin/activate

# Install application dependencies
pip install -r requirements.txt

# Launch the precision oncology dashboard via the cluster proxy configuration
streamlit run app.py --server.port 8501 --server.headless true
```

## 🔬 How it Works

1. **Input:** Paste a raw clinical genomic report into the sidebar.
2. **Inference:** `pipeline.py` routes the text through a customized zero-shot prompt using Llama-3, instructing the model to output a strictly formatted JSON schema.
3. **Rendering:** The app parses the output and populates the dashboard, rendering the Vis.js network graph, updating the Animated Intervention Engine, and plotting the evidence timeline.