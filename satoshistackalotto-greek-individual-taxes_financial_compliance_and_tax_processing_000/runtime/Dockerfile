FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    jq \
    python3 \
    python3-pip \
    python3-venv \
    bash \
    coreutils \
    && rm -rf /var/lib/lib/apt/lists/*

RUN pip3 install pyyaml -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

ENV OPENCLAW_DATA_DIR=/data
WORKDIR /workspace