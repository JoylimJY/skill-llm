FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the workspace and skill directories
RUN mkdir -p /root/.openclaw/workspace/skills/meal-planner \
    && mkdir -p /root/.openclaw/data/meal-planner \
    && mkdir -p /root/.local/bin

WORKDIR /workspace