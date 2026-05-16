FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install jieba -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN git clone https://github.com/smallmj/memory-indexer.git /opt/memory-indexer \
    && cd /opt/memory-indexer \
    && pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple \
    || mkdir -p /opt/memory-indexer

WORKDIR /workspace