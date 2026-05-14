FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    jq \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install requests jsonschema -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the openclaw user and directory structure
RUN useradd -m -s /bin/bash openclaw

RUN mkdir -p /home/openclaw/.openclaw/workspace/governance && \
    mkdir -p /home/openclaw/.openclaw/workspace/evidence && \
    mkdir -p /home/openclaw/.openclaw/workspace/manifests && \
    mkdir -p /home/openclaw/.openclaw/workspace/contracts && \
    mkdir -p /home/openclaw/.openclaw/workspace/clients && \
    mkdir -p /home/openclaw/.openclaw/workspace/archive && \
    chown -R openclaw:openclaw /home/openclaw/.openclaw

WORKDIR /home/openclaw/.openclaw/workspace