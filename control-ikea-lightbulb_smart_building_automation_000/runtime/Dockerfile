FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    bash \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv via pip (pipx alternative for container)
RUN pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple

# Pre-install python-kasa and asyncio support for the mock
RUN pip install python-kasa==0.10.2 asyncio -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace