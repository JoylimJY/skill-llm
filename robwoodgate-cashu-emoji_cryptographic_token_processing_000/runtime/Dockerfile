FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Clone and install cashu-emoji
RUN git clone https://github.com/robwoodgate/cashu-emoji.git /opt/cashu-emoji \
    && cd /opt/cashu-emoji \
    && npm ci

# Make CLI accessible globally
RUN ln -s /opt/cashu-emoji/bin/cashu-emoji.js /usr/local/bin/cashu-emoji \
    && chmod +x /opt/cashu-emoji/bin/cashu-emoji.js

WORKDIR /workspace