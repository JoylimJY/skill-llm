FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    coreutils \
    findutils \
    python3 \
    python3-pip \
    curl \
    wget \
    tar \
    gzip \
    && rm -rf /var/lib/apt/lists/*