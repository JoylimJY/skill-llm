FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    python3 \
    python3-pip \
    curl \
    git \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace

# Create stub loci structure since GitHub is not accessible
RUN mkdir -p /opt/loci/scripts && \
    echo '#!/usr/bin/env node\n// loci stub\n' > /opt/loci/scripts/loci.mjs && \
    chmod +x /opt/loci/scripts/loci.mjs

ENV LOCI_SCRIPT="/opt/loci/scripts/loci.mjs"