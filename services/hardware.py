"""Hardware detection for honest telemetry reporting."""

from __future__ import annotations

import os
import subprocess

import torch


def detect_compute_environment() -> dict:
    """Return real GPU/CPU labels and platform metadata."""
    if torch.cuda.is_available():
        try:
            device_name = torch.cuda.get_device_name(0) or ""
        except Exception:
            device_name = ""

        # ROCm sometimes returns empty string — fall back to rocm-smi
        if not device_name:
            device_name = _rocm_device_name() or "AMD GPU (ROCm)"

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


def _rocm_device_name() -> str:
    """Try rocm-smi to get a human-readable GPU name when PyTorch returns empty."""
    try:
        result = subprocess.run(
            ["rocm-smi", "--showproductname"],
            capture_output=True, text=True, timeout=3, check=False,
        )
        if result.returncode != 0:
            return ""

        gfx_version = ""
        card_sku = ""
        card_series = ""

        for line in result.stdout.splitlines():
            line = line.strip()
            if "GFX Version:" in line:
                gfx_version = line.split(":", 1)[-1].strip()  # e.g. gfx942
            elif "Card SKU:" in line:
                card_sku = line.split(":", 1)[-1].strip()
            elif "Card Series:" in line:
                val = line.split(":", 1)[-1].strip()
                if val and val != "N/A":
                    card_series = val

        # gfx942 = MI300X, gfx940/941 = MI300A, gfx90a = MI250X, gfx908 = MI100
        _GFX_TO_NAME = {
            "gfx942": "AMD Instinct MI300X",
            "gfx941": "AMD Instinct MI300A",
            "gfx940": "AMD Instinct MI300A",
            "gfx90a": "AMD Instinct MI250X",
            "gfx908": "AMD Instinct MI100",
            "gfx906": "AMD Instinct MI60/MI50",
        }

        if card_series:
            return card_series
        if gfx_version and gfx_version in _GFX_TO_NAME:
            return _GFX_TO_NAME[gfx_version]
        if gfx_version:
            return f"AMD GPU ({gfx_version})"

    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return ""


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
