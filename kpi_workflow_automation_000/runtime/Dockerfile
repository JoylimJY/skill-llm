FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    git \
    tree \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install pyyaml regex -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the OpenClaw workspace structure
RUN mkdir -p /root/.openclaw/workspace/memory && \
    mkdir -p /root/.openclaw/workspace/skills && \
    mkdir -p /root/.openclaw/workspace/logs

WORKDIR /workspace