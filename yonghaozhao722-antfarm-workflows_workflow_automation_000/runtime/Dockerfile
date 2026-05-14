FROM node:20-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    sqlite3 \
    curl \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create a mock antfarm CLI that simulates the real tool's behavior deterministically
RUN mkdir -p /root/.openclaw/workspace/antfarm/dist/cli/

# We will write the mock CLI in setup_script via heredoc
WORKDIR /workspace