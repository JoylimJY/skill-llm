FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    bash \
    coreutils \
    findutils \
    grep \
    sed \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages \
    pytest \
    pathlib \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN useradd -m -s /bin/bash researcher && \
    mkdir -p /home/researcher/Downloads && \
    chown -R researcher:researcher /home/researcher

WORKDIR /home/researcher