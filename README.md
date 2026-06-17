# 🧬 BioWeave-AI: Multi-Agent Precision Oncology Engine

> **TCS & AMD Heterogeneous AI Hackathon 2026**
> **Research use only. Not FDA-cleared. Do not use for real clinical decisions.**

BioWeave-AI is a real-time precision oncology platform that takes a raw genomic report and a pathology slide image, runs a three-agent AI pipeline to detect cancer-driving mutations, map signaling pathways, and recommend targeted therapy — with real AutoDock Vina molecular docking scores computed on AMD Instinct MI300X hardware.

---

## Problem Statement

When a cancer patient gets a biopsy, the lab produces a genomic report with mutation details. An oncologist then has to manually search multiple databases to figure out what the mutation means, which pathway it affects, and which drug to use. This process takes hours and requires deep expertise. There is no single tool that connects all these steps automatically. BioWeave-AI solves this by taking the raw report and delivering a complete, evidence-backed treatment recommendation in seconds.

---

## Target Users

- **Oncologists** — fast, evidence-backed therapy recommendations at the point of care
- **Clinical genomics labs** — interpret mutation reports and communicate findings to treating physicians
- **Precision medicine teams** — match patients to targeted therapies based on molecular profiles
- **Cancer research institutions** — accelerate drug discovery and biomarker analysis
- **Hospital tumor boards** — review complex cases where multiple treatment options exist

---

## AI Approach

| Approach | How It Is Used |
|----------|---------------|
| **Multi-Agent AI** | Three specialized agents handle mutation detection, pathway mapping, and therapy matching in sequence |
| **Multimodal AI** | Vision (Phikon ViT) + Text (NER) fused with confidence scoring |
| **Computer Vision** | TCGA-pretrained ViT runs tile-level feature extraction on pathology slides |
| **NLP / NER** | OpenMed biomedical NER extracts gene names and variants from free-text reports |
| **RAG** | Agent 3 retrieves live evidence from ClinVar, CIViC, and OncoKB before recommending therapy |
| **Computational Chemistry** | AutoDock Vina computes real physics-based drug-protein binding affinities |
| **GenAI (optional)** | Llama-3-8B with AWQ 4-bit quantization generates therapeutic rationales on MI300X |

---

## Solution Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                        USER INPUTS                          │
│   📄 Genomic Report (text)    🔬 Pathology Slide (image)   │
└──────────────┬────────────────────────┬─────────────────────┘
               │                        │
               ▼                        ▼
┌──────────────────────┐    ┌───────────────────────┐
│   OpenMed NER +      │    │   Phikon ViT           │
│   Regex Parser       │    │   (TCGA pretrained)    │
│   HIP Stream 1       │    │   HIP Stream 2         │
└──────────┬───────────┘    └──────────┬────────────┘
           └──────────┬────────────────┘
                      │  Multimodal Fusion
                      ▼
         ┌────────────────────────┐
         │   AGENT 1              │
         │   Molecular Detective  │
         │   Mutation ID + Conf.  │
         └────────────┬───────────┘
                      ▼
         ┌────────────────────────┐     ┌─────────────────────┐
         │   AGENT 2              │────▶│  AutoDock Vina 1.2.7│
         │   Pathway Pathologist  │     │  Real Binding       │
         │   Signaling Map        │     │  Affinity (kcal/mol)│
         └────────────┬───────────┘     └─────────────────────┘
                      ▼
         ┌────────────────────────┐
         │   AGENT 3              │
         │   Therapeutic Matchmaker│
         └────────────┬───────────┘
                      │
        ┌─────────────┼──────────────┐
        ▼             ▼              ▼
  ┌──────────┐ ┌──────────┐ ┌──────────────┐
  │ ClinVar  │ │  CIViC   │ │   OncoKB     │
  │ (NCBI)   │ │(GraphQL) │ │ (public API) │
  └──────────┘ └──────────┘ └──────────────┘
                      ▼
         ┌────────────────────────┐
         │   Streamlit Dashboard  │
         │   + FastAPI Backend    │
         └────────────────────────┘
              AMD MI300X / ROCm 7.0
              HIP Dual-Stream GPU
```

---

## Models Used

| Model | Purpose | Parameters |
|-------|---------|------------|
| owkin/phikon | Pathology image feature extraction | ViT-B/16 (~86M) |
| OpenMed NER GenomicDetect | Genomic entity extraction | 109M |
| AutoDock Vina 1.2.7 | Molecular docking — binding affinity | Physics engine |
| Meta Llama-3-8B-Instruct | Therapeutic rationale (optional, AWQ 4-bit) | 8B |
| Regex NER (fallback) | Fast mutation detection without GPU | Rule-based |

---

## Benchmark Results (AMD MI300X)

| Mutation | Drug | Binding Affinity | Latency | Docking Time |
|----------|------|-----------------|---------|--------------|
| BRAF V600E | Dabrafenib | −9.49 kcal/mol | 47.4s* | 13.8s |
| EGFR Exon 19 Del | Osimertinib | −7.36 kcal/mol | 22.3s | 15.7s |
| KRAS G12C | Sotorasib | −9.02 kcal/mol | 7.9s | 6.5s |
| EML4-ALK Fusion | Alectinib | −9.52 kcal/mol | 9.0s | 6.8s |

*First run includes PDB receptor download. Cached runs: ~8s.

GPU: AMD Instinct MI300X (gfx942) | ROCm 7.0 | HIP 6.2 | HIP dual-stream: active

---

## Key Technologies

| Category | Technology |
|----------|------------|
| GPU / Hardware | AMD Instinct MI300X, ROCm 7.0, HIP dual-stream |
| Deep Learning | PyTorch 2.5.1 + ROCm 6.2, HuggingFace Transformers |
| Vision Model | owkin/phikon (ViT-B/16, TCGA pretrained) |
| NER Model | OpenMed NER GenomicDetect (109M, PubMed) |
| Molecular Docking | AutoDock Vina 1.2.7 |
| Ligand Preparation | meeko 0.5, RDKit |
| Clinical APIs | ClinVar (NCBI), CIViC (GraphQL), OncoKB |
| Dashboard | Streamlit, Vis.js, custom glassmorphism CSS |
| Backend | FastAPI, Uvicorn |
| Auth | SHA-256 hashed Bearer tokens |
| Audit Logging | HIPAA-aligned PHI-masking JSONL logger |
| Testing / CI | pytest (80 tests), GitHub Actions, Docker |
| LLM (optional) | Llama-3-8B + AutoAWQ 4-bit on MI300X |

---

## What Was Built During the Hackathon

- Three-agent pipeline with real timing telemetry per agent
- Multimodal fusion — Phikon ViT tile embedding + genomic NER confidence scoring
- AutoDock Vina integration — receptor PDBQT prep, SMILES→ligand conversion, centroid-based binding site detection
- HIP dual-stream parallelization — NER and ViT run concurrently on separate GPU streams
- Live ClinVar, CIViC, and OncoKB evidence retrieval with graceful fallback
- Streamlit dashboard — six UI components including animated network graph and docking simulation panel
- FastAPI backend with API key auth, audit middleware, and admin endpoints
- HIPAA-aligned audit logger with automatic PHI masking
- AWQ/GPTQ quantized LLM loader for Llama-3 on MI300X
- 80-test pytest suite covering NER, pipeline, docking, API, and audit logging
- GitHub Actions CI — test, lint, Docker build on every push
- Docker multi-stage build — ROCm and CPU targets

---

## Project Structure

```text
├── app.py                       # Streamlit dashboard
├── pipeline.py                  # Three-agent orchestration
├── api/
│   ├── main.py                  # FastAPI REST backend
│   └── auth.py                  # API key authentication
├── services/
│   ├── ner.py                   # OpenMed NER + regex
│   ├── vision.py                # owkin/phikon pathology ViT
│   ├── wsi_tiler.py             # Slide tiling (Pillow)
│   ├── docking.py               # AutoDock Vina engine
│   ├── docking_targets.py       # PDB binding site definitions
│   ├── hip_parallel.py          # HIP dual-stream parallelization
│   ├── llm_quantized.py         # AWQ/GPTQ quantized LLM loader
│   ├── audit_log.py             # HIPAA audit logger
│   ├── clinvar_client.py        # NCBI E-utilities
│   ├── civic_client.py          # CIViC GraphQL
│   ├── oncokb_client.py         # OncoKB API
│   ├── evidence.py              # Aggregates all APIs
│   ├── clinical_kb.py           # Curated mutation profiles
│   ├── hardware.py              # Real GPU detection
│   └── config.py                # Central configuration
├── components/                  # Streamlit UI components
├── data/                        # Demo case JSON profiles
├── tests/                       # pytest suite (80 tests)
├── Dockerfile                   # Multi-stage: ROCm + CPU
├── docker-compose.yml
├── pyproject.toml               # pytest + ruff config
└── .github/workflows/ci.yml     # GitHub Actions CI
```

---

## Quick Start

```bash
git clone https://github.com/bharathi16112-png/BioWeave-AI.git
cd BioWeave-AI
pip install -r requirements.txt

# Enable live docking
pip install vina meeko rdkit prody

# Dashboard (local)
streamlit run app.py --server.port 8501

# Dashboard (cluster / remote)
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# REST API
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Validate Installation

```bash
python validate.py
# Expected: ALL CHECKS PASSED
```

## Run Tests

```bash
pytest tests/ -v          # 80 tests
pytest tests/ --cov=.     # with coverage
```

---

## Configuration

Copy `.env.example` to `.env`:

```bash
NCBI_API_KEY=8822d326fc42e73d38d0d378c35d16c12b08
BIOWEAVE_CONTACT_EMAIL=bharathi16112@gmail.com
BIOWEAVE_ENABLE_DOCKING=true
BIOWEAVE_DOCKING_EXHAUSTIVENESS=12

# Optional LLM on MI300X
BIOWEAVE_LLM_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
BIOWEAVE_LLM_QUANT=awq
```

## Docker

```bash
docker compose up                    # CPU / dev
docker compose --profile rocm up     # AMD ROCm MI300X
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | — | Liveness check |
| GET | `/demo-profiles` | — | List demo cases |
| POST | `/analyze/text` | optional | Text inference |
| POST | `/analyze/multimodal` | optional | Text + image |
| GET | `/admin/health-detail` | required | System info |
| POST | `/admin/generate-key` | required | Provision API key |

---

## What Is Real vs. Curated

| Component | Status | Notes |
|-----------|--------|-------|
| Genomic NER | ✅ Real | OpenMed ML + regex |
| Pathology ViT | ✅ Real | owkin/phikon visual screening |
| HIP dual-stream | ✅ Real | NER + ViT concurrent on MI300X |
| AutoDock Vina | ✅ Real | Physics-based docking, real PDB structures |
| ClinVar / CIViC | ✅ Real | Live free APIs |
| OncoKB | ✅ Real | Public/demo API |
| API auth | ✅ Real | SHA-256 Bearer tokens |
| HIPAA audit log | ✅ Real | Append-only JSONL, PHI masked |
| LLM rationale | ✅ Real | Optional — needs `BIOWEAVE_LLM_MODEL` |
| WSI OpenSlide | 🔜 Next | Pillow tiling done; `.svs` needs openslide-python |
| Pathology ViT fine-tune | 🔜 Next | Classification head needs TCGA fine-tuning |

---

## Future Extensions

- Fine-tune Phikon classifier head for mutation subtype from image alone
- OpenSlide integration for gigapixel `.svs` whole-slide images
- FastAPI + PostgreSQL for multi-patient case management
- HIPAA-compliant deployment with OAuth2 institutional SSO
- Expanded mutation coverage beyond the current 4 profiles

---

## License & Disclaimer

Research and hackathon use only. Not for clinical diagnosis or treatment. All models and APIs used are free and open source.
