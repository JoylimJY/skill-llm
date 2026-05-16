FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    jq \
    python3 \
    python3-pip \
    curl \
    coreutils \
    findutils \
    grep \
    sed \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages python-dateutil -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN useradd -m -s /bin/bash agent

RUN mkdir -p /workspace && chown agent:agent /workspace && chmod 777 /workspace

WORKDIR /home/agent