FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    bash \
    nodejs \
    npm \
    python3 \
    python3-pip \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Configure git globally so bd sync/commit works
RUN git config --global user.email "agent@test.local" && \
    git config --global user.name "Test Agent" && \
    git config --global init.defaultBranch main