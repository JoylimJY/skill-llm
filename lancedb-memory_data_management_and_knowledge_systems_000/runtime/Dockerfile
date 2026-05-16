FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    lancedb==0.5.4 \
    pyarrow==14.0.2 \
    pandas==2.1.4 \
    numpy==1.26.4 \
    python-dateutil==2.9.0 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace