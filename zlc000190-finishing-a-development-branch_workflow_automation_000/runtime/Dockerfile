FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    bash \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest pydantic --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install a fake 'gh' CLI that simulates GitHub CLI behavior for PR creation
# We will write it in setup_script

RUN git config --global user.email "agent@test.local" && \
    git config --global user.name "Agent Test" && \
    git config --global init.defaultBranch main