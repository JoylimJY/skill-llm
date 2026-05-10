FROM node:18-bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages requests -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace/skill_context
COPY . /workspace/skill_context/

RUN if [ ! -f package.json ]; then npm init -y; fi && npm install --prefix /workspace/skill_context

WORKDIR /workspace