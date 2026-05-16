FROM python:3.10-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pandas==2.1.4 \
    numpy==1.26.4 \
    scikit-learn==1.4.0 \
    scipy==1.12.0 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace