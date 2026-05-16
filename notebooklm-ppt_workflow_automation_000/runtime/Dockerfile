FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    jq \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    python-pptx \
    requests \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the openclaw inbound directory
RUN mkdir -p /root/.openclaw/media/inbound

WORKDIR /workspace