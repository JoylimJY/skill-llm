FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    python3 \
    python3-pip \
    nodejs \
    npm \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install flask requests --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN npm install -g mcporter --registry https://registry.npmmirror.com

RUN mkdir -p /workspace
WORKDIR /workspace