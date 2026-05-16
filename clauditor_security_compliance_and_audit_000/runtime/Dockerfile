FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    pkg-config \
    libssl-dev \
    git \
    sudo \
    python3 \
    python3-pip \
    ca-certificates \
    rustc \
    cargo \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.cargo/bin:${PATH}"

# Copy clauditor source from local build context
COPY . /opt/clauditor

WORKDIR /workspace