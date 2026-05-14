FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    bash \
    python3 \
    python3-pip \
    sudo \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18 via NodeSource
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user with sudo access (systemctl --user needs a real user)
RUN useradd -m -s /bin/bash agent && \
    echo "agent ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Create workspace directory
RUN mkdir -p /workspace && chown agent:agent /workspace

# Set up git global config for the agent user
USER agent
RUN git config --global user.email "agent@test.local" && \
    git config --global user.name "Agent Test" && \
    git config --global init.defaultBranch main

USER root
WORKDIR /workspace