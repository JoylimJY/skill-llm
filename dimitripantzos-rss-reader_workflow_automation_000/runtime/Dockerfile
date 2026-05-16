FROM node:18-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install requests -i https://pypi.tuna.tsinghua.edu.cn/simple

# Set up the workspace root
WORKDIR /root/clawd

# Install rss-reader node dependencies
RUN mkdir -p /root/clawd/skills/rss-reader/scripts && \
    cd /root/clawd/skills/rss-reader && \
    npm init -y && \
    npm install xml2js node-fetch@2