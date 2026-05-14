FROM node:20-bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install the agent-traffic-analyzer tool globally from npm
RUN npm install -g agent-traffic-analyzer --registry https://registry.npmjs.org

WORKDIR /workspace