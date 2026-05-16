FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    gcc \
    libc6-dev \
    python3 \
    python3-pip \
    build-essential \
    coreutils \
    findutils \
    grep \
    && rm -rf /var/lib/apt/lists/*