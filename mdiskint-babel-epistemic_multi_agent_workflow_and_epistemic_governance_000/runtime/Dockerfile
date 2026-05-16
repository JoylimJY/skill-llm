FROM node:20-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g babel-validate --registry https://registry.npmmirror.com 2>/dev/null || npm install -g babel-validate

RUN pip3 install jsonschema pyyaml --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace