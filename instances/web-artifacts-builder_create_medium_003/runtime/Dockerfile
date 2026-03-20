FROM node:20-slim

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/cache/apt/archives /var/lib/apt/lists/*

RUN npm install -g pnpm

WORKDIR /workspace

RUN pip3 install --break-system-packages beautifulsoup4 lxml requests

COPY . .

RUN if [ -d "scripts" ] && [ -n "$(find scripts -name '*.sh' -type f 2>/dev/null)" ]; then \
        chmod +x scripts/*.sh; \
    fi