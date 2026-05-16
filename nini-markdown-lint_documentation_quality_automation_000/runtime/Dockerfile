FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    bash \
    git \
    nodejs \
    npm \
    python3 \
    python3-pip \
    gawk \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g markdownlint-cli2 --registry https://registry.npmmirror.com

RUN pip3 install pre-commit -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

WORKDIR /workspace