FROM node:20-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install requests --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple

# Pre-install socket.io-client globally and in the expected temp location
RUN mkdir -p /tmp/mol-im-bot && cd /tmp/mol-im-bot && npm init -y --silent && npm install socket.io-client --silent

# Install socket.io server for mock
RUN mkdir -p /opt/mock-server && cd /opt/mock-server && npm init -y --silent && npm install socket.io express --silent

WORKDIR /workspace