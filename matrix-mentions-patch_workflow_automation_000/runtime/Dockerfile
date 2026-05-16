FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    bash \
    grep \
    python3 \
    python3-pip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 22 via nvm-style directory structure
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Create the NVM-style directory structure that the skill expects
RUN mkdir -p /root/.nvm/versions/node/v22.22.0/bin && \
    ln -sf $(which node) /root/.nvm/versions/node/v22.22.0/bin/node && \
    ln -sf $(which npm) /root/.nvm/versions/node/v22.22.0/bin/npm

ENV HOME=/root
WORKDIR /root