FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    jq \
    cron \
    && rm -rf /var/lib/apt/lists/*

RUN pip install lunarcalendar pytz -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create a mock 'openclaw' CLI that logs all calls to a file
RUN mkdir -p /usr/local/bin

RUN printf '%s\n' \
    '#!/usr/bin/env python3' \
    'import sys' \
    'import os' \
    'import json' \
    'from datetime import datetime' \
    '' \
    'log_path = os.path.expanduser("~/.openclaw/call_log.jsonl")' \
    'os.makedirs(os.path.dirname(log_path), exist_ok=True)' \
    '' \
    'args = sys.argv[1:]' \
    'entry = {' \
    '    "timestamp": datetime.now().isoformat(),' \
    '    "args": args' \
    '}' \
    '' \
    'with open(log_path, "a") as f:' \
    '    f.write(json.dumps(entry, ensure_ascii=False) + "\n")' \
    '' \
    'print(f"[mock openclaw] called with: {\" \".join(args)}")' \
    > /usr/local/bin/openclaw

RUN chmod +x /usr/local/bin/openclaw

WORKDIR /workspace