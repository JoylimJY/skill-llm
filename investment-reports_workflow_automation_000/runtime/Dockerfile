FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    postgresql \
    postgresql-client \
    sudo \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install psycopg2-binary pandas yfinance -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create workspace directory
RUN mkdir -p /workspace

WORKDIR /workspace