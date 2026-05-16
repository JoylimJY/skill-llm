FROM python:3.10-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN pip install \
    numpy \
    scipy \
    sentence-transformers \
    torch \
    transformers \
    huggingface_hub \
    requests \
    pytest \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace