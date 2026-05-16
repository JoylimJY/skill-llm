FROM node:20-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    git \
    curl \
    python3 \
    python3-pip \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g reskill --registry https://registry.npmjs.org || true

RUN git config --global user.email "agent@test.local" && \
    git config --global user.name "Agent Test"

WORKDIR /workspace