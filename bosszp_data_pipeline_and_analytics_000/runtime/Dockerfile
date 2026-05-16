FROM python:3.10-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    default-mysql-server \
    default-mysql-client \
    libmariadb-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    scrapy \
    flask \
    pandas \
    sqlalchemy \
    pymysql \
    cryptography \
    jieba \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN pip install \
    flash \
    -i https://pypi.tuna.tsinghua.edu.cn/simple || true

WORKDIR /workspace