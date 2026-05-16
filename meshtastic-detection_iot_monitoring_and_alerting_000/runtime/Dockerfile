FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    jq \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install meshtastic skill dependencies
RUN pip install \
    meshtastic \
    pypubsub \
    python-dateutil \
    pyserial \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace