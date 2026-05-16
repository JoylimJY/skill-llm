FROM rust:1.78-slim-bookworm

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    pkg-config \
    libssl-dev \
    python3 \
    python3-pip \
    ripgrep \
    && rm -rf /var/lib/apt/lists/*

# Install cargo-tarpaulin for coverage
RUN cargo install cargo-tarpaulin --locked 2>/dev/null || true

# Install a stub 'ralph' CLI that records emitted events to a file
RUN mkdir -p /usr/local/bin

# Pre-warm the Rust registry cache for common crates
RUN cargo search serde 2>/dev/null || true

WORKDIR /workspace