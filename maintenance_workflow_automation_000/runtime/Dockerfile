FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    jq \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# Install the maintenance skill from npm-style or direct shell install
# Based on the SKILL.md metadata (bytesagain), install via bash installer pattern
RUN pip3 install maintenance 2>/dev/null || true

# Try to install via npm global if available
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/* || true
RUN npm install -g maintenance 2>/dev/null || true

# Clone and install from source as fallback
RUN git clone https://github.com/bytesagain/ai-skills /opt/ai-skills 2>/dev/null || true
RUN if [ -f /opt/ai-skills/install.sh ]; then bash /opt/ai-skills/install.sh; fi || true

# Ensure bash is default shell
SHELL ["/bin/bash", "-c"]

WORKDIR /workspace