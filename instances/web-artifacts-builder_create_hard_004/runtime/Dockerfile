FROM node:20-slim

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g pnpm

WORKDIR /workspace

RUN pip3 install --break-system-packages beautifulsoup4 lxml requests