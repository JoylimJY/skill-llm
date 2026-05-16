FROM node:18-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    curl \
    tar \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the openclaw skill directory structure
RUN mkdir -p /root/.openclaw/workspace/skills/openclaw-backup/scripts \
    && mkdir -p /root/.openclaw/workspace/skills/openclaw-backup/references \
    && mkdir -p /root/.openclaw/workspace/skills/openclaw-backup/config \
    && mkdir -p /root/backups/openclaw

WORKDIR /root/.openclaw/workspace/skills/openclaw-backup

# Install npm dependencies
RUN npm init -y && npm install fs-extra tar commander dayjs \
    --registry https://registry.npmmirror.com

WORKDIR /root