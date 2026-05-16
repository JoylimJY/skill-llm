FROM node:18-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    jq \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the openclaw workspace structure
RUN mkdir -p /root/.openclaw/workspace/skills/long-task-monitor \
    && mkdir -p /root/.openclaw/workspace/long-tasks \
    && mkdir -p /root/.openclaw/extensions

WORKDIR /workspace