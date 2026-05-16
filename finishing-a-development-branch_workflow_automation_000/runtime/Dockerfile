FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install a mock 'gh' CLI that simulates PR creation
RUN mkdir -p /usr/local/bin

# Configure git globally
RUN git config --global user.email "agent@test.local" && \
    git config --global user.name "Test Agent" && \
    git config --global init.defaultBranch main

WORKDIR /workspace