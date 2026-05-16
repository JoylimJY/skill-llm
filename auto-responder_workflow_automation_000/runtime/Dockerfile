FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    nodejs \
    npm \
    bash \
    curl \
    jq \
    tree \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install jsonschema -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

# Create a mock auto-responder CLI that validates the config and simulates behavior
RUN mkdir -p /usr/local/bin