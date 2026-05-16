FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    coreutils \
    gawk \
    sqlite3 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install pandas faker -i https://pypi.tuna.tsinghua.edu.cn/simple