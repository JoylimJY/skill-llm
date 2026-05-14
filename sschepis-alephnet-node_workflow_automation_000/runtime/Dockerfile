FROM node:20-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    jq \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /opt/alephnet-node

# Install the alephnet-node package globally
RUN npm install -g @sschepis/alephnet-node 2>/dev/null || true

# Also install locally so CLI is available
RUN npm install @sschepis/alephnet-node 2>/dev/null || true

# Ensure the CLI is available
RUN npm install -g @sschepis/alephnet-node || npm install @sschepis/alephnet-node

RUN ln -sf $(npm root -g)/@sschepis/alephnet-node/bin/alephnet-node /usr/local/bin/alephnet-node 2>/dev/null || true

WORKDIR /workspace

RUN mkdir -p /workspace