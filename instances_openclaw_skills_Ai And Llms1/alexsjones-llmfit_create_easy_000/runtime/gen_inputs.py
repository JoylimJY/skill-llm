from pathlib import Path
import json

Path('workspace_marker.txt').write_text('LLMFIT_ADVISOR_MARKER\nAPPLE_M2_MAX_32GB\nAVAILABLE_24_5GB\n', encoding='utf-8')

system = {
    'system': {
        'cpu_name': 'Apple M2 Max',
        'cpu_cores': 12,
        'total_ram_gb': 32.0,
        'available_ram_gb': 24.5,
        'has_gpu': True,
        'gpu_name': 'Apple M2 Max',
        'gpu_vram_gb': 32.0,
        'gpu_count': 1,
        'backend': 'Metal',
        'unified_memory': True,
    }
}

recommendations = {
    'models': [
        {
            'name': 'Qwen/Qwen2.5-Coder-7B-Instruct',
            'provider': 'Qwen',
            'params_b': 7,
            'score': 96,
            'score_components': {'quality': 94, 'speed': 95, 'fit': 100, 'context': 92},
            'fit_level': 'Perfect',
            'run_mode': 'GPU',
            'best_quant': 'Q5_K_M',
            'estimated_tps': 62,
            'memory_required_gb': 8.2,
            'memory_available_gb': 32.0,
            'utilization_pct': 25.6,
            'use_case': 'coding',
            'context_length': 32768,
        },
        {
            'name': 'deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct',
            'provider': 'DeepSeek',
            'params_b': 16,
            'score': 91,
            'score_components': {'quality': 96, 'speed': 82, 'fit': 94, 'context': 91},
            'fit_level': 'Good',
            'run_mode': 'GPU',
            'best_quant': 'Q4_K_M',
            'estimated_tps': 38,
            'memory_required_gb': 13.9,
            'memory_available_gb': 32.0,
            'utilization_pct': 43.4,
            'use_case': 'coding',
            'context_length': 16384,
        },
        {
            'name': 'mistralai/Mistral-7B-Instruct-v0.3',
            'provider': 'Mistral',
            'params_b': 7,
            'score': 88,
            'score_components': {'quality': 88, 'speed': 90, 'fit': 97, 'context': 85},
            'fit_level': 'Perfect',
            'run_mode': 'GPU',
            'best_quant': 'Q5_K_M',
            'estimated_tps': 68,
            'memory_required_gb': 7.6,
            'memory_available_gb': 32.0,
            'utilization_pct': 23.8,
            'use_case': 'coding',
            'context_length': 32768,
        },
    ]
}

Path('system.json').write_text(json.dumps(system, indent=2), encoding='utf-8')
Path('recommendations.json').write_text(json.dumps(recommendations, indent=2), encoding='utf-8')
