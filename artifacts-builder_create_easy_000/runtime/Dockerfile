FROM node:20-slim

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    git \
    python3 \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g pnpm

WORKDIR /workspace
