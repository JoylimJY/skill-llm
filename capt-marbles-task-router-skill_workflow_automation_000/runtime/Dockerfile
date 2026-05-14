FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    bash \
    curl \
    wget \
    git \
    jq \
    nano \
    vim \
    less \
    tree \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pyyaml python-dateutil -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN useradd -ms /bin/bash agent
USER agent
WORKDIR /home/agent

ENV HOME=/home/agent
ENV PATH="/home/agent/.local/bin:$PATH"