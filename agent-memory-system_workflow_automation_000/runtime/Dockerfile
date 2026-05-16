FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    coreutils \
    python3 \
    python3-pip \
    findutils \
    grep \
    sed \
    gawk \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install python-dateutil pyyaml -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

WORKDIR /workspace