FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    bash \
    python3 \
    python3-pip \
    nodejs \
    npm \
    file \
    && rm -rf /var/lib/apt/lists/*

# Install leak-cli globally via npm
RUN npm install -g leak-cli --registry https://registry.npmjs.org || true

WORKDIR /workspace