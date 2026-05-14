FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    jq \
    sqlite3 \
    python3 \
    python3-pip \
    ca-certificates \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install consensus-tools globally from npm
RUN npm install -g @consensus-tools/consensus-tools \
    --registry https://registry.npmjs.org \
    || npm install -g @consensus-tools/consensus-tools

# Install python evaluation dependencies
RUN pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace