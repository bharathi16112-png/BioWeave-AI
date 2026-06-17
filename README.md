# BioWeave-AI: Multi-Agent Precision Oncology Reasoning Platform

BioWeave-AI is an advanced multi-agent reasoning platform built on the **AMD Instinct MI300X** acceleration platform using the **ROCm v6.x compute stack**. It extracts complex genomic signatures from raw clinical oncology text reports and maps them to dynamic signaling pathway intervention models and therapeutic matchmakers.

## 🚀 System Architecture
- **Molecular Detective Agent:** Extracts variant configurations (BRAF, EGFR, KRAS, ALK).
- **Pathway Pathologist Agent:** Visualizes biological signaling cascades using interactive Vis.js graphs.
- **Therapeutic Matchmaker Agent:** Validates drug exclusions, counterfactual logic, and database-linked evidence timelines.

## ⚡ AMD Instinct Acceleration Benchmarks
- **Hardware:** AMD Instinct MI300X (240GB VRAM)
- **Software Stack:** Native PyTorch with ROCm/HIP compilation
- **Performance:** Sub-second multi-agent trace parsing (~450ms–490ms total latency)

## 🛠️ Installation & Local Cluster Startup
```bash
# Clone the repository
git clone https://github.com/bharathi16112-png/BioWeave-AI.git
cd BioWeave-AI

# Activate virtual environment and install dependencies
source /workspace/shared/bio_env/bin/activate
pip install -r requirements.txt

# Run the app locally via AMD container port mapping
streamlit run app.py --server.port 8501 --server.headless true
```