# ─────────────────────────────────────────────────────────────────────────────
# BioWeave-AI — Production Docker Image
# Base: rocm/pytorch for AMD MI300X / ROCm  |  fallback to CPU for dev
#
# Build for AMD ROCm (MI300X cluster):
#   docker build --target rocm -t bioweave-ai:rocm .
#
# Build for CPU / CI (no GPU required):
#   docker build --target cpu -t bioweave-ai:cpu .
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: ROCm GPU target ─────────────────────────────────────────────────
FROM rocm/pytorch:rocm6.2_ubuntu22.04_py3.10_pytorch_release_2.3.0 AS rocm

LABEL org.opencontainers.image.title="BioWeave-AI (ROCm)"
LABEL org.opencontainers.image.description="Precision oncology multi-agent AI — AMD MI300X"
LABEL org.opencontainers.image.version="2.0.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    # ROCm GPU visibility — override per container if needed
    HIP_VISIBLE_DEVICES=0 \
    # HuggingFace model cache inside container
    HF_HOME=/app/.cache/huggingface \
    # BioWeave config
    BIOWEAVE_CONTACT_EMAIL=bharathi16112@gmail.com \
    BIOWEAVE_ENABLE_DOCKING=true

WORKDIR /app

# System deps for OpenSlide (future WSI) and docking prep
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libgomp1 \
        openslide-tools \
        && rm -rf /var/lib/apt/lists/*

# Python deps — copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    # Docking stack (optional — comment out if not needed)
    pip install --no-cache-dir vina meeko rdkit || echo "Docking stack optional — skipping"

# Copy source
COPY . .

# Non-root user for security
RUN useradd -m -u 1000 bioweave && chown -R bioweave:bioweave /app
USER bioweave

# Verify smoke test (regex-only, no ML download needed)
RUN BIOWEAVE_DISABLE_ML=true python validate.py

EXPOSE 8501 8000

# Default: run both Streamlit dashboard and FastAPI API via a simple launcher
# Override CMD to run only one service
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port 8000 & streamlit run app.py --server.port 8501 --server.address 0.0.0.0"]


# ── Stage 2: CPU-only target (CI, dev, no GPU) ───────────────────────────────
FROM python:3.11-slim AS cpu

LABEL org.opencontainers.image.title="BioWeave-AI (CPU)"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BIOWEAVE_DISABLE_ML=true \
    BIOWEAVE_ENABLE_DOCKING=false \
    BIOWEAVE_CONTACT_EMAIL=bharathi16112@gmail.com

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1-mesa-glx \
        libglib2.0-0 \
        && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir httpx pytest pytest-cov

COPY . .

RUN useradd -m -u 1000 bioweave && chown -R bioweave:bioweave /app
USER bioweave

RUN python validate.py

EXPOSE 8501 8000

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port 8000 & streamlit run app.py --server.port 8501 --server.address 0.0.0.0"]
