FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pyyaml python-dateutil --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace