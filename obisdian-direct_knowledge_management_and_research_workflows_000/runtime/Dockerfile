FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    ripgrep \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pyyaml python-dateutil thefuzz[speedup] -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the vault directory and skills directory
RUN mkdir -p /home/ruslan/webdav/data/ruslain/.obsidian
RUN mkdir -p /home/ruslan/.openclaw/workspace/skills/obsidian/scripts

ENV OBSIDIAN_VAULT=/home/ruslan/webdav/data/ruslain

WORKDIR /workspace