FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    bash \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install pyyaml -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN git config --global user.email "dev@fintech-corp.com" && \
    git config --global user.name "Li Wei"

WORKDIR /workspace