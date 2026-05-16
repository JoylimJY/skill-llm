FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    rsync \
    python3 \
    python3-pip \
    coreutils \
    findutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

# Create the workspace and skill directories
RUN mkdir -p /root/.openclaw/workspace/skills/obsidian-folder-sync/scripts \
    && mkdir -p /root/.openclaw/workspace/logs

WORKDIR /workspace