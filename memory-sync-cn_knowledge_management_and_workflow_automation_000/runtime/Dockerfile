FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    jq \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

RUN pip install cortexgraph -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN npm install -g mcporter

# Ensure bins are accessible
RUN which cortexgraph || echo "cortexgraph not in PATH"
RUN which mcporter || echo "mcporter not in PATH"

WORKDIR /workspace