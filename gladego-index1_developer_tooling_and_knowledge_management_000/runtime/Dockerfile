FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install index1 and supporting packages
RUN pip install index1 -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install pytest requests -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace