import os
import random
import stat

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep nested distractor structure ---
distractor_dirs = [
    "cluster/node01/logs",
    "cluster/node01/config",
    "cluster/node02/logs",
    "cluster/node02/config",
    "monitoring/dashboards",
    "monitoring/alerts",
    "training_jobs/job_001",
    "training_jobs/job_002",
    "training_jobs/job_003",
    "scripts/legacy",
    "scripts/utils",
    "reports/weekly",
    "reports/monthly",
    "docs/internal",
]

for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "cluster/node01/logs/system.log": "INFO: Node started\nINFO: Connected to scheduler\nWARN: High memory usage detected",
    "cluster/node01/config/node.yaml": "node_id: node01\ncpus: 32\nram_gb: 256\nstatus: active",
    "cluster/node02/logs/system.log": "INFO: Node started\nERROR: GPU driver version mismatch",
    "cluster/node02/config/node.yaml": "node_id: node02\ncpus: 64\nram_gb: 512\nstatus: degraded",
    "monitoring/dashboards/gpu_dashboard.json": '{"type": "dashboard", "panels": ["gpu_temp", "gpu_util", "mem_usage"]}',
    "monitoring/alerts/oom_alert.yaml": "alert: OOMKill\ncondition: vram_used > 0.95 * vram_total\nseverity: critical",
    "training_jobs/job_001/config.json": '{"model": "resnet50", "batch_size": 128, "gpu_id": 0}',
    "training_jobs/job_002/config.json": '{"model": "bert-large", "batch_size": 16, "gpu_id": 1}',
    "training_jobs/job_003/config.json": '{"model": "gpt2", "batch_size": 8, "gpu_id": 0}',
    "scripts/legacy/old_monitor.sh": "#!/bin/bash\n# Deprecated: use new monitoring stack\nwhile true; do free -m; sleep 5; done",
    "scripts/utils/cleanup.py": "import os\ndef clean_tmp():\n    pass  # TODO: implement",
    "reports/weekly/week_42.csv": "date,gpu_util,avg_temp\n2024-10-14,78,71\n2024-10-15,82,73",
    "reports/monthly/october.txt": "October GPU Utilization Report\nAverage utilization: 79%\nPeak temperature: 84C",
    "docs/internal/gpu_policy.md": "# GPU Usage Policy\n- Maximum job runtime: 24h\n- Memory reservation required\n- No idle GPU tolerance",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- Mock nvidia-smi binary ---
# This script simulates the exact nvidia-smi CLI interface
mock_nvidia_smi = r"""#!/usr/bin/env python3
import sys
import os

# Simulated GPU data
GPUS = [
    {"id": 0, "name": "NVIDIA A100-SXM4-80GB", "uuid": "GPU-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
     "temp": 62, "perf": "P0", "power_used": 312, "power_cap": 400,
     "mem_used": 61440, "mem_total": 81920, "gpu_util": 87, "fan": "N/A"},
    {"id": 1, "name": "NVIDIA A100-SXM4-80GB", "uuid": "GPU-b2c3d4e5-f6a7-8901-bcde-f12345678901",
     "temp": 71, "perf": "P0", "power_used": 398, "power_cap": 400,
     "mem_used": 79872, "mem_total": 81920, "gpu_util": 99, "fan": "N/A"},
    {"id": 2, "name": "NVIDIA A100-SXM4-80GB", "uuid": "GPU-c3d4e5f6-a7b8-9012-cdef-123456789012",
     "temp": 45, "perf": "P8", "power_used": 28, "power_cap": 400,
     "mem_used": 512, "mem_total": 81920, "gpu_util": 0, "fan": "N/A"},
]

COMPUTE_APPS = [
    {"pid": 12345, "process_name": "/usr/bin/python3", "gpu_id": 0, "used_memory": 58000},
    {"pid": 12346, "process_name": "/usr/bin/python3", "gpu_id": 1, "used_memory": 42000},
    {"pid": 12347, "process_name": "/opt/conda/bin/python", "gpu_id": 1, "used_memory": 37000},
    {"pid": 9999,  "process_name": "/usr/bin/Xorg", "gpu_id": 2, "used_memory": 512},
]

args = sys.argv[1:]

# nvidia-smi -L
if args == ['-L']:
    for g in GPUS:
        print(f"GPU {g['id']}: {g['name']} (UUID: {g['uuid']})")
    sys.exit(0)

# nvidia-smi --query-compute-apps=... --format=csv...
if any('--query-compute-apps' in a for a in args) and any('--format' in a for a in args):
    query_arg = [a for a in args if '--query-compute-apps' in a][0]
    fields_str = query_arg.split('=', 1)[1]
    fields = [f.strip() for f in fields_str.split(',')]
    
    noheader = '--format=csv,noheader' in ' '.join(args) or 'noheader' in ' '.join(args)
    nounits = 'nounits' in ' '.join(args)
    
    if not noheader:
        print(', '.join(fields))
    
    for app in COMPUTE_APPS:
        row = []
        for f in fields:
            if f == 'pid':
                row.append(str(app['pid']))
            elif f == 'process_name':
                row.append(app['process_name'])
            elif f == 'used_memory' or f == 'used_gpu_memory':
                if nounits:
                    row.append(str(app['used_memory']))
                else:
                    row.append(f"{app['used_memory']} MiB")
            elif f == 'gpu_uuid':
                row.append(GPUS[app['gpu_id']]['uuid'])
            else:
                row.append('[N/A]')
        print(', '.join(row))
    sys.exit(0)

# nvidia-smi -q -d MEMORY,POWER  or  nvidia-smi -q -d MEMORY  etc.
if '-q' in args:
    gpu_filter = None
    if '-i' in args:
        idx = args.index('-i')
        gpu_filter = int(args[idx+1])
    
    show_memory = True
    show_power = True
    if '-d' in args:
        idx = args.index('-d')
        d_val = args[idx+1].upper()
        categories = [c.strip() for c in d_val.split(',')]
        show_memory = 'MEMORY' in categories
        show_power = 'POWER' in categories
    
    target_gpus = GPUS if gpu_filter is None else [GPUS[gpu_filter]]
    
    for g in target_gpus:
        print(f"GPU {g['id']}")
        print(f"    Product Name                          : {g['name']}")
        if show_memory:
            print(f"    FB Memory Usage")
            print(f"        Total                         : {g['mem_total']} MiB")
            print(f"        Used                          : {g['mem_used']} MiB")
            print(f"        Free                          : {g['mem_total'] - g['mem_used']} MiB")
        if show_power:
            print(f"    Power Readings")
            print(f"        Power Draw                    : {g['power_used']}.00 W")
            print(f"        Power Limit                   : {g['power_cap']}.00 W")
    sys.exit(0)

# Default output
print("+" + "-"*78 + "+")
print("| NVIDIA-SMI 525.89.02    Driver Version: 525.89.02    CUDA Version: 12.0     |")
print("+" + "-"*19 + "+" + "-"*19 + "+" + "-"*37 + "+")
print("| GPU  Name        Temp Perf   Pwr:Usage/Cap|       Memory-Usage | GPU-Util  |")
print("|===============================+======================+======================|")
for g in GPUS:
    mem_str = f"{g['mem_used']}MiB / {g['mem_total']}MiB"
    print(f"|  {g['id']}  {g['name'][:16]:<16}  {g['temp']}C  {g['perf']:<4}  {g['power_used']:>3}W / {g['power_cap']}W | {mem_str:>20} | {g['gpu_util']:>7}% |")
print("+" + "-"*78 + "+")
print("")
print("| Processes:                                                                  |")
print("|  GPU   GI   CI        PID   Type   Process name              GPU Memory    |")
for app in COMPUTE_APPS:
    print(f"|   {app['gpu_id']}    N/A  N/A  {app['pid']:>7}      C   {app['process_name']:<26} {app['used_memory']:>6}MiB |")
print("+" + "-"*78 + "+")
sys.exit(0)
"""

mock_nvidia_smi_path = os.path.join(workspace, "scripts", "mock_nvidia_smi.py")
with open(mock_nvidia_smi_path, "w") as f:
    f.write(mock_nvidia_smi)
os.chmod(mock_nvidia_smi_path, 0o755)

# --- Mock pynvml module ---
# Placed in workspace/mock_libs/pynvml.py — agent must use the real installed pynvml,
# but we override it by installing a fake one at the system level via setup_script
mock_pynvml = '''"""
Mock pynvml for testing environment.
Simulates 3 NVIDIA A100 GPUs.
"""

NVML_TEMPERATURE_GPU = 0

class NVMLError(Exception):
    pass

_GPUS = [
    {
        "name": b"NVIDIA A100-SXM4-80GB",
        "temp": 62,
        "power_mw": 312000,
        "mem_used": 64424509440,
        "mem_total": 85899345920,
        "util_gpu": 87,
        "util_mem": 72,
    },
    {
        "name": b"NVIDIA A100-SXM4-80GB",
        "temp": 71,
        "power_mw": 398000,
        "mem_used": 83755311104,
        "mem_total": 85899345920,
        "util_gpu": 99,
        "util_mem": 98,
    },
    {
        "name": b"NVIDIA A100-SXM4-80GB",
        "temp": 45,
        "power_mw": 28000,
        "mem_used": 536870912,
        "mem_total": 85899345920,
        "util_gpu": 0,
        "util_mem": 0,
    },
]

class _Handle:
    def __init__(self, idx):
        self._idx = idx

class _MemInfo:
    def __init__(self, used, total):
        self.used = used
        self.total = total
        self.free = total - used

class _Utilization:
    def __init__(self, gpu, memory):
        self.gpu = gpu
        self.memory = memory

def nvmlInit():
    pass

def nvmlShutdown():
    pass

def nvmlDeviceGetCount():
    return len(_GPUS)

def nvmlDeviceGetHandleByIndex(index):
    if index < 0 or index >= len(_GPUS):
        raise NVMLError(f"Invalid index {index}")
    return _Handle(index)

def nvmlDeviceGetName(handle):
    return _GPUS[handle._idx]["name"]

def nvmlDeviceGetTemperature(handle, sensor_type):
    return _GPUS[handle._idx]["temp"]

def nvmlDeviceGetPowerUsage(handle):
    return _GPUS[handle._idx]["power_mw"]

def nvmlDeviceGetMemoryInfo(handle):
    g = _GPUS[handle._idx]
    return _MemInfo(g["mem_used"], g["mem_total"])

def nvmlDeviceGetUtilizationRates(handle):
    g = _GPUS[handle._idx]
    return _Utilization(g["util_gpu"], g["util_mem"])
'''

mock_pynvml_dir = os.path.join(workspace, "mock_libs")
os.makedirs(mock_pynvml_dir, exist_ok=True)
with open(os.path.join(mock_pynvml_dir, "pynvml.py"), "w") as f:
    f.write(mock_pynvml)

# --- Task briefing file (business context, no technical hints) ---
briefing = """GPU FLEET HEALTH AUDIT - REQUIREMENTS BRIEF
============================================
Date: 2024-10-28
Requestor: MLOps Platform Team

BACKGROUND:
Our GPU training cluster has been experiencing resource contention issues. 
Several training jobs have been failing with out-of-memory errors, and we 
suspect zombie processes are not releasing VRAM after job completion.

DELIVERABLES NEEDED:

1. A shell script named 'audit_gpus.sh' that:
   - Lists all GPUs with their unique identifiers
   - Collects memory and power data for all GPUs
   - Produces a CSV report of all compute processes currently consuming GPU memory
     (capturing: process ID, process name, and memory used)
   - Saves this CSV to 'process_report.csv' in the same directory as the script

2. A Python script named 'gpu_health_report.py' that:
   - Connects to the GPU management library
   - Iterates over all available GPUs
   - For each GPU, collects: name, temperature (Celsius), power consumption (Watts),
     memory used (MB), total memory (MB), and GPU compute utilization (%)
   - Flags any GPU where power consumption exceeds 390W as 'power_critical'
   - Flags any GPU where memory utilization exceeds 90% as 'memory_critical'  
   - Saves a structured JSON file named 'gpu_health_report.json' with all findings

The scripts should work with the monitoring tools already installed on this server.
"""

with open(os.path.join(workspace, "TASK_BRIEF.txt"), "w") as f:
    f.write(briefing)

# More distractors
with open(os.path.join(workspace, "training_jobs/job_001/run.log"), "w") as f:
    f.write("Epoch 1/100: loss=2.341\nEpoch 2/100: loss=2.109\nCUDA out of memory. Tried to allocate 2.50 GiB\n")

with open(os.path.join(workspace, "training_jobs/job_002/run.log"), "w") as f:
    f.write("Epoch 1/50: loss=1.876\nEpoch 2/50: loss=1.654\nEpoch 3/50: loss=1.432\n")

with open(os.path.join(workspace, "cluster/node01/config/scheduler.yaml"), "w") as f:
    f.write("scheduler: slurm\nmax_jobs_per_gpu: 2\npreemption: enabled\n")

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")