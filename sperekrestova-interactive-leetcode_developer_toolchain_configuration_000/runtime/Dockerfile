FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    jq \
    file \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pyyaml -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create a non-root user to simulate a real developer environment
RUN useradd -m -s /bin/bash devuser
USER devuser
WORKDIR /home/devuser