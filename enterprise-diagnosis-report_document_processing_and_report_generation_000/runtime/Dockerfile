FROM python:3.10-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    build-essential \
    libmupdf-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    PyMuPDF==1.23.26 \
    requests==2.31.0 \
    reportlab==4.1.0 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace