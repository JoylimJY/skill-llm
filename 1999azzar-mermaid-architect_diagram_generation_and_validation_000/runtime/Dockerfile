FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    nodejs \
    npm \
    python3 \
    python3-pip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @mermaid-js/mermaid-cli@10.6.1 --prefer-offline || \
    npm install -g @mermaid-js/mermaid-cli@10.6.1

RUN pip3 install --break-system-packages \
    pyyaml \
    -i https://pypi.tuna.tsinghua.edu.cn/simple