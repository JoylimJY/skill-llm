FROM node:22-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    python3-pip \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install requests flask --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple || \
    pip3 install requests flask -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install neon-soul globally from npm
RUN npm install -g neon-soul 2>/dev/null || true

# Create workspace
RUN mkdir -p /workspace
WORKDIR /workspace