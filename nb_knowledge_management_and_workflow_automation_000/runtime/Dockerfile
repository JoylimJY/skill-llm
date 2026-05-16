FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    bats \
    pandoc \
    ripgrep \
    w3m \
    xclip \
    ncat \
    netcat-openbsd \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install nb CLI
RUN bash -c "$(curl -fsSL https://raw.githubusercontent.com/xwmx/nb/master/nb)" -- install 2>/dev/null || true
RUN curl -fsSL https://raw.githubusercontent.com/xwmx/nb/master/nb -o /usr/local/bin/nb && chmod +x /usr/local/bin/nb

# Configure git (required for nb)
RUN git config --global user.email "agent@test.local" && \
    git config --global user.name "Agent Test" && \
    git config --global init.defaultBranch main

# Create workspace directory
RUN mkdir -p /workspace

WORKDIR /workspace