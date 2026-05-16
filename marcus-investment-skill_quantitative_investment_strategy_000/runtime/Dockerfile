FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    sqlite3 \
    bc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pandas numpy -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN mkdir -p /root/.openclaw/workspace/skills/marcus-investment-analyst/scripts \
    && mkdir -p /root/.openclaw/workspace/skills/marcus-investment-analyst/references \
    && mkdir -p /root/.openclaw/workspace/skills/marcus-investment-analyst/assets \
    && mkdir -p /root/.openclaw/workspace/memory/stock-analysis \
    && mkdir -p /root/data \
    && mkdir -p /workspace