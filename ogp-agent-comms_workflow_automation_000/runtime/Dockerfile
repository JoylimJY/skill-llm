FROM node:20-bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install OGP globally
RUN npm install -g github:dp-pcs/ogp --ignore-scripts 2>/dev/null || true

WORKDIR /workspace