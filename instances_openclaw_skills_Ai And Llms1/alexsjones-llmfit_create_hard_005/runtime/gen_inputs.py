from pathlib import Path
import json

# Deterministic input generation with embedded markers
workspace = Path('.')

system = {
    "system": {
        "cpu_name": "Apple M2 Max",
        "cpu_cores": 12,
        "total_ram_gb": 32.0,
        "available_ram_gb": 24.5,
        "has_gpu": True,
        "gpu_name": "Apple M2 Max",
        "gpu_vram_gb": 32.0,
        "gpu_count": 1,
        "backend": "Metal",
        "unified_memory": True,
        "marker": "HWMARKER-ALPHA-2025"
    }
}

recommendations = {
    "models": [
        {
            "name": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "provider": "Qwen",
            "params_b": 7,
            "score": 96,
            "score_components": {"quality": 95, "speed": 94, "fit": 98, "context": 96},
            "fit_level": "Perfect",
            "run_mode": "GPU",
            "best_quant": "Q6_K_M",
            "estimated_tps": 42.1,
            "memory_required_gb": 7.8,
            "memory_available_gb": 32.0,
            "utilization_pct": 24.4,
            "use_case": "coding",
            "context_length": 32768,
            "marker": "REC-MARKER-CODE-001"
        },
        {
            "name": "meta-llama/Llama-3.1-8B-Instruct",
            "provider": "Meta",
            "params_b": 8,
            "score": 94,
            "score_components": {"quality": 93, "speed": 93, "fit": 97, "context": 92},
            "fit_level": "Perfect",
            "run_mode": "GPU",
            "best_quant": "Q6_K_M",
            "estimated_tps": 39.5,
            "memory_required_gb": 8.4,
            "memory_available_gb": 32.0,
            "utilization_pct": 26.2,
            "use_case": "chat",
            "context_length": 128000,
            "marker": "REC-MARKER-CHAT-002"
        },
        {
            "name": "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
            "provider": "DeepSeek",
            "params_b": 16,
            "score": 90,
            "score_components": {"quality": 92, "speed": 84, "fit": 91, "context": 93},
            "fit_level": "Good",
            "run_mode": "GPU",
            "best_quant": "Q5_K_M",
            "estimated_tps": 24.0,
            "memory_required_gb": 15.6,
            "memory_available_gb": 32.0,
            "utilization_pct": 48.8,
            "use_case": "coding",
            "context_length": 16384,
            "marker": "REC-MARKER-CODE-003"
        }
    ],
    "marker": "REC-MARKER-ROOT-999"
}

Path('system.json').write_text(json.dumps(system, indent=2), encoding='utf-8')
Path('recommendations.json').write_text(json.dumps(recommendations, indent=2), encoding='utf-8')
Path('openclaw_template.json').write_text(json.dumps({"models": {"providers": {"ollama": {"models": []}}}, "agents": {"defaults": {"model": {"primary": ""}}}}, indent=2), encoding='utf-8')
