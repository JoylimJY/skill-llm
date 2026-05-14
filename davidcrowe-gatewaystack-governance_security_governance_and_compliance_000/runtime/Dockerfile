FROM node:20-bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    git \
    jq \
    tree \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create a working user with home dir
RUN useradd -m -s /bin/bash agentuser
USER agentuser
WORKDIR /home/agentuser/workspace

# Set npm prefix so global installs go to user home
ENV NPM_CONFIG_PREFIX=/home/agentuser/.npm-global
ENV PATH="/home/agentuser/.npm-global/bin:${PATH}"