"""Hardware detection for honest telemetry reporting."""

from __future__ import annotations

import os
import subprocess

import torch


def detect_compute_environment() -> dict:
    """Return real GPU/CPU labels and platform metadata."""
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        vram_gb = round(torch.cuda.memory_allocated(0) / 1e9, 2)
        device_count = torch.cuda.device_count()
        platform = _detect_platform_label()
        return {
            "gpu_hardware": device_name,
            "compute_platform": platform,
            "vram_allocated_gb": vram_gb,
            "device_count": device_count,
            "using_gpu": True,
        }

    return {
        "gpu_hardware": "CPU (no CUDA/ROCm device detected)",
        "compute_platform": "PyTorch CPU",
        "vram_allocated_gb": 0.0,
        "device_count": 0,
        "using_gpu": False,
    }


def _detect_platform_label() -> str:
    """Best-effort ROCm vs CUDA labeling."""
    rocm_version = os.environ.get("ROCM_VERSION")
    if rocm_version:
        return f"ROCm {rocm_version} (HIP)"

    try:
        result = subprocess.run(
            ["rocm-smi", "--showproductname"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return "ROCm (HIP)"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    if hasattr(torch.version, "hip") and torch.version.hip:
        return f"ROCm HIP {torch.version.hip}"

    cuda_version = getattr(torch.version, "cuda", None)
    if cuda_version:
        return f"CUDA {cuda_version}"

    return "PyTorch GPU (unknown stack)"
