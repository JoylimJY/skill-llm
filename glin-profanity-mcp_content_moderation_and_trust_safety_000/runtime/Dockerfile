FROM node:20-bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Pre-install the glin-profanity-mcp and core library so the agent doesn't need to wait
RUN npm install -g glin-profanity-mcp glin-profanity 2>/dev/null || true

# Pre-cache npx so it doesn't need to download at runtime
RUN npx -y glin-profanity-mcp --version 2>/dev/null || true

RUN pip3 install --break-system-packages \
    numpy \
    -i https://pypi.tuna.tsinghua.edu.cn/simple || \
    pip3 install --break-system-packages numpy || true

WORKDIR /workspace