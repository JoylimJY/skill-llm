FROM node:20-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    git \
    bash \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install memory-palace globally via npx (will be fetched on first use)
# Pre-install to avoid cold-start delays
RUN npm install -g memory-palace@1.6.5 2>/dev/null || true

WORKDIR /workspace