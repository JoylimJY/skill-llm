FROM python:3.12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN pip install akshare pandas numpy requests lxml openpyxl -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace