FROM node:18-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace

ENV HOME=/root
ENV OPENCLAW_WORKSPACE=/root/.openclaw/workspace