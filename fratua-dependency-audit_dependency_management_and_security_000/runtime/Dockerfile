FROM node:20-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install pip-audit and other Python tooling
RUN pip3 install pip-audit packaging -i https://pypi.tuna.tsinghua.edu.cn/simple

# Ensure npm and npx are available (already in node:20)
RUN npm install -g npm@10

WORKDIR /workspace