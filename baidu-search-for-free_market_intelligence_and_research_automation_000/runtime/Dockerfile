FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    requests \
    beautifulsoup4 \
    lxml \
    flask \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create workspace
RUN mkdir -p /workspace/scripts /workspace/baidusearch /workspace/reports /workspace/data /workspace/logs \
    /workspace/archive/2023/q1 /workspace/archive/2023/q2 /workspace/archive/2024/q1 \
    /workspace/config /workspace/tmp /workspace/cache

WORKDIR /workspace