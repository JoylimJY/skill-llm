FROM node:20-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    sqlite3 \
    curl \
    bash \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the standard openclaw directory structure
RUN mkdir -p /root/.openclaw/workspace/state \
    && mkdir -p /root/.openclaw/extensions \
    && mkdir -p /root/.openclaw/logs

WORKDIR /workspace