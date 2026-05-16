FROM python:3.10-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    python-docx \
    markdown \
    beautifulsoup4 \
    PyPDF2 \
    numpy \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace