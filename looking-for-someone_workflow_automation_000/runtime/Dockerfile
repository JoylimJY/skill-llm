FROM node:18-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace

RUN npm install -g openclaw 2>/dev/null || true

# Clone the looking-for-someone skill
RUN git clone https://github.com/openclaw/looking-for-someone.git /workspace/looking-for-someone 2>/dev/null || \
    (mkdir -p /workspace/looking-for-someone && echo '{}' > /workspace/looking-for-someone/package.json)

WORKDIR /workspace/looking-for-someone

RUN npm install 2>/dev/null || true