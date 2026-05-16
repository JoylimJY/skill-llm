FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    wget \
    git \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

RUN pip install python-docx lxml -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create workspace and skill directory structure
RUN mkdir -p /workspace \
    && mkdir -p /root/.openclaw/workspace/skills/docx-formatter/examples

WORKDIR /workspace