FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    nmap \
    sudo \
    iproute2 \
    net-tools \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages requests -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace