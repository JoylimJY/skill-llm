FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN git clone https://github.com/meimakes/deep-current /workspace/deep-current-skill

WORKDIR /workspace