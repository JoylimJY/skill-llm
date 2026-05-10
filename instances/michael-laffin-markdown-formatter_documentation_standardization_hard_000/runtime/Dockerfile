FROM node:18-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace/skill_context
COPY . /workspace/skill_context/
RUN npm install 2>/dev/null || true

WORKDIR /workspace