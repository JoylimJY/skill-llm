FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install flask requests beautifulsoup4 lxml -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create output directory
RUN mkdir -p /mnt/user-data/outputs

WORKDIR /workspace