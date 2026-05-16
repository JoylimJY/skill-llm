FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    python3 \
    python3-pip \
    coreutils \
    grep \
    sed \
    findutils \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages colorsys 2>/dev/null || true

WORKDIR /workspace