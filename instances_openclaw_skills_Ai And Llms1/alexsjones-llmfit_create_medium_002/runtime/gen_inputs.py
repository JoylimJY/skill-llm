from pathlib import Path
import json

hardware = {
    "system": {
        "cpu_name": "Test CPU X",
        "cpu_cores": 16,
        "total_ram_gb": 64.0,
        "available_ram_gb": 52.5,
        "has_gpu": True,
        "gpu_name": "Test GPU Y",
        "gpu_vram_gb": 24.0,
        "gpu_count": 1,
        "backend": "CUDA",
        "unified_memory": False,
    }
}

recommendations = {
    "models": [
        {
            "name": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "provider": "Qwen",
            "params_b": 7,
            "score": 94,
            "score_components": {"quality": 92, "speed": 96, "fit": 98, "context": 90},
            "fit_level": "Perfect",
            "run_mode": "GPU",
            "best_quant": "Q6_K_M",
            "estimated_tps": 68.2,
            "memory_required_gb": 6.8,
            "memory_available_gb": 24.0,
            "utilization_pct": 28.3,
            "use_case": "coding",
            "context_length": 32768,
        },
        {
            "name": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
            "provider": "DeepSeek",
            "params_b": 32,
            "score": 79,
            "score_components": {"quality": 98, "speed": 45, "fit": 72, "context": 88},
            "fit_level": "Good",
            "run_mode": "CPU+GPU Offload",
            "best_quant": "Q4_K_M",
            "estimated_tps": 19.4,
            "memory_required_gb": 22.1,
            "memory_available_gb": 24.0,
            "utilization_pct": 92.1,
            "use_case": "reasoning",
            "context_length": 16384,
        },
        {
            "name": "mistralai/Mistral-7B-Instruct-v0.3",
            "provider": "Mistral",
            "params_b": 7,
            "score": 88,
            "score_components": {"quality": 84, "speed": 93, "fit": 95, "context": 80},
            "fit_level": "Perfect",
            "run_mode": "GPU",
            "best_quant": "Q5_K_M",
            "estimated_tps": 72.0,
            "memory_required_gb": 5.9,
            "memory_available_gb": 24.0,
            "utilization_pct": 24.6,
            "use_case": "general",
            "context_length": 32768,
        },
    ]
}

Path("hardware.json").write_text(json.dumps(hardware, indent=2), encoding="utf-8")
Path("recommendations.json").write_text(json.dumps(recommendations, indent=2), encoding="utf-8")
Path("markers.txt").write_text("MARKER:LLMFIT-ADV-001\nMARKER:RECOMMENDATION-SET-A\n", encoding="utf-8")