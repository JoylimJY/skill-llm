FROM node:20-bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    bash \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytz python-dateutil -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install truetime skill dependencies
RUN npm install -g luxon