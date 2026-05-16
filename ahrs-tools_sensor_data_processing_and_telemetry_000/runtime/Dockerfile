FROM python:3.10-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list 2>/dev/null || true && \
    apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install numpy pywayne qmt -i https://pypi.tuna.tsinghua.edu.cn/simple