FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    git \
    bash \
    python3 \
    python3-pip \
    sudo \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Create the patron user and required directory structure
RUN useradd -m -s /bin/bash patron && \
    mkdir -p /home/patron/apps/_bin /home/patron/apps/_logs /home/patron/apps/_state && \
    chown -R patron:patron /home/patron/apps && \
    echo 'patron ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

WORKDIR /home/patron

# Pre-cache npm packages to speed up create-expo-app (best effort)
RUN npm config set cache /home/patron/.npm-cache || true