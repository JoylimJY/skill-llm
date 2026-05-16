FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    fontconfig \
    fonts-liberation \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install python-pptx Pillow lxml -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN mkdir -p /usr/local/share/fonts/poppins /usr/local/share/fonts/lora

RUN fc-cache -fv || true

WORKDIR /workspace