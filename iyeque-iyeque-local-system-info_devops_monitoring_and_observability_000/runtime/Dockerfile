FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv psutil -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the skill directory and the sysinfo.py script
RUN mkdir -p /workspace/skills/local-system-info

# Write the sysinfo.py script
RUN cat > /workspace/skills/local-system-info/sysinfo.py << 'PYEOF'
#!/usr/bin/env python3
"""Local system info skill - returns system metrics as JSON."""
import sys
import json
import psutil

def get_cpu():
    load = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0.0, 0.0, 0.0]
    cpu_count = psutil.cpu_count(logical=True)
    normalized = [round(x / cpu_count, 4) for x in load]
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "cpu_count": cpu_count,
        "load_avg": normalized
    }

def get_memory():
    vm = psutil.virtual_memory()
    sw = psutil.swap_memory()
    return {
        "total": vm.total,
        "available": vm.available,
        "percent": vm.percent,
        "swap_percent": sw.percent
    }

def get_disk():
    du = psutil.disk_usage('/')
    return {
        "total": du.total,
        "used": du.used,
        "free": du.free,
        "percent": du.percent
    }

def get_processes(limit=20):
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
        try:
            info = p.info
            procs.append({
                "pid": info['pid'],
                "name": info['name'] or "",
                "username": info['username'] or "",
                "cpu_percent": info['cpu_percent'] or 0.0,
                "memory_percent": round(info['memory_percent'] or 0.0, 4)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x['cpu_percent'], reverse=True)
    return procs[:limit]

def get_summary():
    return {
        "cpu": get_cpu(),
        "memory": get_memory(),
        "disk": get_disk()
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["summary", "cpu", "memory", "disk", "processes"])
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    if args.action == "summary":
        result = get_summary()
    elif args.action == "cpu":
        result = get_cpu()
    elif args.action == "memory":
        result = get_memory()
    elif args.action == "disk":
        result = get_disk()
    elif args.action == "processes":
        result = get_processes(args.limit)

    print(json.dumps(result, indent=2))
PYEOF

WORKDIR /workspace