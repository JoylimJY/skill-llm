FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    make \
    curl \
    vim \
    tree \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    pyyaml \
    toml \
    pytest \
    ruff \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace