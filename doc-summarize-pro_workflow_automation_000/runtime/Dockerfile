FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    python3 \
    python3-pip \
    coreutils \
    findutils \
    grep \
    sed \
    gawk \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace