FROM node:20-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    jq \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace

# Pre-install the npm package globally so it's available
RUN npm install -g consensus-code-merge-guard --registry https://registry.npmjs.org || true

# Also install tsx globally as the skill requires it
RUN npm install -g tsx --registry https://registry.npmjs.org || true