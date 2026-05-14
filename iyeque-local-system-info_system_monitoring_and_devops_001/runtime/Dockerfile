FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    bash \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip install psutil uv -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace