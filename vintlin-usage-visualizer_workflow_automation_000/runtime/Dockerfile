FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    libasound2 \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    flask \
    jinja2 \
    pillow \
    matplotlib \
    pandas \
    numpy \
    pytz \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace