FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    bash \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install \
    requests \
    click \
    rich \
    pydantic \
    python-dateutil \
    pathlib2 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN useradd -m -s /bin/bash agent && \
    mkdir -p /home/agent/project && \
    chown -R agent:agent /home/agent/project

WORKDIR /home/agent/project