FROM node:20-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    git \
    curl \
    python3 \
    python3-pip \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install skillstore globally from the openclaw ecosystem
# We clone the openclaw-skills repo which contains skillstore
RUN git clone https://github.com/openclaw/skills.git /opt/openclaw-skills || true

WORKDIR /workspace
ENV HOME=/root