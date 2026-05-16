FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    bash \
    grep \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages python-dateutil -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN git config --global user.email "agent@test.local" && \
    git config --global user.name "Test Agent"

WORKDIR /workspace