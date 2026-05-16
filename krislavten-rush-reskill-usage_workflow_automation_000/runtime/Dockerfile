FROM node:20-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    curl \
    wget \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install reskill globally
RUN npm install -g reskill --registry https://registry.npmmirror.com || npm install -g reskill

# Install git-http-backend and a simple HTTP server for mock git
RUN apt-get update && apt-get install -y git apache2-utils fcgiwrap nginx && rm -rf /var/lib/apt/lists/* || true

# Python tools for eval
RUN pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

# Configure git global identity
RUN git config --global user.email "test@test.com" && git config --global user.name "Test"
RUN git config --global init.defaultBranch main

WORKDIR /workspace