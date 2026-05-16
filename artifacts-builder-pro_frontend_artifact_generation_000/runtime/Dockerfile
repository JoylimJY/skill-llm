FROM node:20-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    bash \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install beautifulsoup4 lxml -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace