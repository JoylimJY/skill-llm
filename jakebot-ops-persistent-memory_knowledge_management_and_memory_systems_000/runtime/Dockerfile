FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Pre-install heavy ML deps at image level so the venv setup is faster
RUN pip install --no-cache-dir \
    chromadb==0.4.24 \
    networkx==3.2.1 \
    sentence-transformers==2.7.0 \
    torch==2.2.2 \
    transformers==4.40.2 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace