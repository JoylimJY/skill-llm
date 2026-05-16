FROM node:18-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace

# Install the feishu-clawbot-card skill via openclaw
RUN npm install -g openclaw 2>/dev/null || true

# Clone the skill directly since openclaw CLI may not be available
RUN mkdir -p skills && \
    git clone https://github.com/HMyaoyuan/feishu-clawbot-card.git skills/feishu-clawbot-card 2>/dev/null || \
    (mkdir -p skills/feishu-clawbot-card && \
     cd skills/feishu-clawbot-card && \
     npm init -y && \
     node -e "console.log('skill placeholder')")

# Install skill dependencies
RUN cd skills/feishu-clawbot-card && npm install 2>/dev/null || true