FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    nodejs \
    npm \
    python3 \
    python3-pip \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install pnpm globally
RUN npm install -g pnpm --registry https://registry.npmmirror.com

# Install Python evaluation dependencies
RUN pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

# Configure git globally
RUN git config --global user.email "agent@devteam.local" && \
    git config --global user.name "Developer Agent" && \
    git config --global init.defaultBranch main