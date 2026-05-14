FROM node:18-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    grep \
    findutils \
    && rm -rf /var/lib/apt/lists/*

# Install pip-audit and supporting Python tools
RUN pip3 install pip-audit packaging -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install global npm tools
RUN npm install -g npm@9.9.3

# Pre-install depcheck so npx can find it
RUN npm install -g depcheck

WORKDIR /workspace