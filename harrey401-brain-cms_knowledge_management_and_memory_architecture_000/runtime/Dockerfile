FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    git \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install lancedb numpy pyarrow requests sentence-transformers -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the workspace structure
RUN mkdir -p /workspace/memory_brain /workspace/memory/schemas

WORKDIR /workspace