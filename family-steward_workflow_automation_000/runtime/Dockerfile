FROM node:18-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install requests python-dateutil -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace

RUN mkdir -p /workspace/family-steward/data && \
    mkdir -p /workspace/family-steward/bin

WORKDIR /workspace/family-steward

RUN echo '{"name":"family-steward","version":"1.0.0","description":"Family Steward management system","main":"index.js","bin":{"steward":"./bin/steward.js"},"scripts":{"build":"tsc"},"dependencies":{"commander":"^11.0.0","uuid":"^9.0.0"},"devDependencies":{"typescript":"^5.0.0","@types/node":"^18.0.0","@types/uuid":"^9.0.0"}}' > package.json

WORKDIR /workspace