# 🧬 BioWeave-AI: Multi-Agent Precision Oncology Engine

BioWeave-AI is a precision oncology platform built for the **AMD Heterogeneous AI Hackathon (2026)**. It runs a three-agent clinical workflow using **100% free, open-source resources** — no paid APIs required.

> **Research use only.** Not FDA-cleared. Do not use for real clinical decisions.

## Implementation Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Honesty & correctness fixes | ✅ Complete |
| Phase 2 | Real inference core (NER, Phikon ViT, live APIs) | ✅ Complete |
| Phase 3 | AutoDock Vina molecular docking | ✅ Complete |
| Phase 4 | Production hardening | ✅ Complete |

## Architecture

```text
Genomic Text ──► OpenMed NER + Regex ──────────────────────────┐
                 (HIP Stream 1 on MI300X)                       │
                                                                ▼
Pathology Image ──► Phikon ViT + Tiling ──────────────► Agent 1: Molecular Detective
                    (HIP Stream 2 on MI300X)                    │
                                                                ▼
                                                       Agent 2: Pathway Pathologist
                                                      AutoDock Vina docking (kcal/mol)
                                                      PDB co-crystal binding sites
                                                                │
                                                                ▼
                                                       Agent 3: Therapeutic Matchmaker
                                                                │
                                            ┌───────────────────┼────────────────────┐
                                            ▼                   ▼                    ▼
                                        ClinVar              CIViC               OncoKB
                                       (NCBI)             (GraphQL)          (demo/public)
                                                                │
                                                         FastAPI Backend
                                                     (API key auth + audit log)
                                                                │
                                                    Streamlit Dashboard UI
```

## Free Resources Used

| Component | Free Resource | Cost |
|-----------|---------------|------|
| Pathology ViT | [owkin/phikon](https://huggingface.co/owkin/phikon) (TCGA) | $0 |
| Genomic NER | [OpenMed NER](https://huggingface.co/OpenMed/OpenMed-NER-GenomicDetect-PubMed-109M) | $0 |
| Molecular docking | [AutoDock Vina](https://github.com/ccsb-scripps/AutoDock-Vina) | $0 |
| Ligand prep | [meeko](https://github.com/forlilab/Meeko) + [RDKit](https://www.rdkit.org/) | $0 |
| ClinVar evidence | [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/clinvar/docs/programmatic_access/) | $0 |
| Therapeutic evidence | [CIViC GraphQL API](https://civicdb.org/api/graphql) | $0 |
| Drug/pathway data | [OncoKB demo/public API](https://api.oncokb.org/) | $0 |
| UI | Streamlit + Vis.js | $0 |
| Backend | FastAPI + Uvicorn | $0 |

Optional free keys: `NCBI_API_KEY`, `ONCOKB_API_TOKEN` (academic).

## Project Structure

```text
├── app.py                       # Streamlit dashboard
├── pipeline.py                  # Three-agent orchestration
├── api/
│   ├── main.py                  # FastAPI REST backend (auth + audit)
│   └── auth.py                  # API key Bearer token authentication
├── services/
│   ├── ner.py                   # OpenMed NER + regex
│   ├── vision.py                # owkin/phikon pathology ViT
│   ├── wsi_tiler.py             # Slide tiling (Pillow)
│   ├── docking.py               # AutoDock Vina engine (Phase 3)
│   ├── docking_targets.py       # PDB binding site definitions
│   ├── hip_parallel.py          # HIP/CUDA dual-stream parallelization
│   ├── llm_quantized.py         # AWQ/GPTQ/BnB quantized LLM loader
│   ├── audit_log.py             # HIPAA-aligned PHI-masking audit logger
│   ├── clinvar_client.py        # NCBI E-utilities
│   ├── civic_client.py          # CIViC GraphQL
│   ├── oncokb_client.py         # OncoKB demo/public
│   ├── evidence.py              # Aggregates all free APIs
│   ├── clinical_kb.py           # Curated mutation profiles
│   ├── hardware.py              # Real GPU detection
│   ├── llm_agent.py             # Optional LLM rationale enrichment
│   └── config.py                # Central configuration
├── components/                  # Streamlit UI components
├── data/                        # Demo case JSON profiles
├── tests/                       # pytest test suite (80 tests)
│   ├── conftest.py
│   ├── test_ner.py
│   ├── test_pipeline.py
│   ├── test_clinical_kb.py
│   ├── test_api.py
│   └── test_audit_log.py
├── Dockerfile                   # Multi-stage: ROCm + CPU targets
├── docker-compose.yml           # Dashboard + API services
├── pyproject.toml               # pytest + ruff config
└── .github/workflows/ci.yml     # GitHub Actions CI
```

## Quick Start

```bash
git clone https://github.com/bharathi16112-png/BioWeave-AI.git
cd BioWeave-AI
pip install -r requirements.txt

# Dashboard
streamlit run app.py --server.port 8501

# REST API (optional)
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Enable Live Molecular Docking (Phase 3)

Install via conda (recommended — prebuilt binaries):
```bash
conda install -c conda-forge vina meeko rdkit
```
Or pip:
```bash
pip install vina meeko rdkit
```
On first analysis run, receptor PDB files are downloaded from RCSB (~200KB each) and cached to `~/.cache/bioweave/docking/`. Subsequent runs use the cache.

## Enable Quantized LLM (MI300X / ROCm)

```bash
# AWQ — best on ROCm/AMD (preferred)
pip install autoawq

# Set model in .env
BIOWEAVE_LLM_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
BIOWEAVE_LLM_QUANT=awq   # or gptq / bnb / none
```
Reduces VRAM from ~16GB (fp16) to ~5-6GB (4-bit AWQ).

## Docker

```bash
# CPU / development
docker compose up

# AMD ROCm (MI300X cluster)
docker compose --profile rocm up
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | — | Liveness check |
| GET | `/demo-profiles` | — | List demo cases |
| GET | `/demo-profiles/{name}` | — | Get demo case |
| POST | `/analyze/text` | optional | Text inference |
| POST | `/analyze/multimodal` | optional | Text + image |
| GET | `/admin/health-detail` | required | Detailed system info |
| POST | `/admin/generate-key` | required | Provision API key |

Enable auth by setting `BIOWEAVE_API_KEYS=<hash1>,<hash2>` (SHA-256 hashes). Generate key pairs:
```bash
curl -X POST http://localhost:8000/admin/generate-key \
  -H "Authorization: Bearer <admin_key>"
```

## Testing

```bash
# Full suite (80 tests, ~70s)
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=term-missing

# Fast smoke test (no pytest needed)
python validate.py
```

## Configuration

Copy `.env.example` to `.env`:

```bash
# Pre-configured with your keys
NCBI_API_KEY=8822d326fc42e73d38d0d378c35d16c12b08
BIOWEAVE_CONTACT_EMAIL=bharathi16112@gmail.com

# Optional
ONCOKB_API_TOKEN=your_academic_token

# Docking
BIOWEAVE_ENABLE_DOCKING=true
BIOWEAVE_DOCKING_EXHAUSTIVENESS=12   # higher = more thorough

# HIPAA audit log path
BIOWEAVE_AUDIT_LOG_PATH=/var/log/bioweave/audit.jsonl

# API auth (SHA-256 hashes of keys)
BIOWEAVE_API_KEYS=hash1,hash2

# Quantized LLM (GPU required)
BIOWEAVE_LLM_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
BIOWEAVE_LLM_QUANT=awq
```

## What Is Real vs. Curated

| Component | Status | Notes |
|-----------|--------|-------|
| Genomic NER | ✅ Real | OpenMed ML + regex |
| Pathology ViT | ✅ Real | owkin/phikon (visual screening only; text required for mutation ID) |
| NER + ViT parallelism | ✅ Real | HIP/CUDA dual-stream on GPU; thread-pool on CPU |
| AutoDock Vina docking | ✅ Real | Requires `vina meeko rdkit`; falls back to curated scores |
| Binding site coords | ✅ Real | From published co-crystal PDB structures (4XV2, 4ZAU, 6OIM, 3AOX) |
| Pathway suppression | ✅ Real | Sigmoid model calibrated to published IC50 data |
| ClinVar / CIViC evidence | ✅ Real | Live free APIs |
| Drug recommendations | ✅ Real | OncoKB public/demo API |
| LLM rationale | ✅ Real | Optional; requires `BIOWEAVE_LLM_MODEL` |
| AWQ quantization | ✅ Real | Requires `autoawq` + GPU |
| API auth | ✅ Real | SHA-256 hashed Bearer tokens |
| HIPAA audit log | ✅ Real | Append-only JSONL with PHI masking |
| WSI OpenSlide | 🔜 Next | Pillow tiling is implemented; `.svs` needs openslide-python |
| Pathology-tuned ViT | 🔜 Next | Phikon is foundation model; mutation classification head needs fine-tuning |

## License & Disclaimer

Research and hackathon use only. Not for clinical diagnosis or treatment.
