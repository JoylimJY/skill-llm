FROM node:18-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    jq \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install ethers.js for the wallet scripts
RUN npm install ethers

# Install Python packages for eval
RUN pip3 install eth-account eth-utils -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages