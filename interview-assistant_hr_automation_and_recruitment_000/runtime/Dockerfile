FROM node:18-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install the interview-assistant CLI tool globally
RUN npm install -g interview-assistant --registry https://registry.npmmirror.com

WORKDIR /workspace