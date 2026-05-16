FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    jq \
    tree \
    && rm -rf /var/lib/apt/lists/*

RUN pip install requests beautifulsoup4 lxml markdown -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace