FROM node:18-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    sqlite3 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install requests -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install memory-engine globally and also in a known location
RUN npm install -g memory-engine 2>/dev/null || true

WORKDIR /workspace

RUN npm install memory-engine 2>/dev/null || true