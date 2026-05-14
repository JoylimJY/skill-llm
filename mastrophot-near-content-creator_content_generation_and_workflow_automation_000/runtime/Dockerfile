FROM node:20-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install requests -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install the near-content-creator skill globally from npm
RUN npm install -g near-content-creator 2>/dev/null || true

# Also try to install locally in a known path for the skill
RUN mkdir -p /skills/near-content-creator && \
    cd /skills/near-content-creator && \
    npm init -y && \
    npm install near-content-creator 2>/dev/null || true

WORKDIR /workspace