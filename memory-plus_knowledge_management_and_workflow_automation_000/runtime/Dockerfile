FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install requests jieba -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create openclaw workspace structure
RUN mkdir -p /root/.openclaw/workspace/skills/memory-workflow/scripts
RUN mkdir -p /root/.openclaw/workspace/memory-workflow-data/memories
RUN mkdir -p /root/.openclaw/workspace/memory-workflow-data/knowledge-graph

WORKDIR /root/.openclaw/workspace/skills/memory-workflow