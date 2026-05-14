FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    bash \
    python3 \
    python3-pip \
    nodejs \
    npm \
    sqlite3 \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @consensus-tools/consensus-tools --registry https://registry.npmjs.org

RUN pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace