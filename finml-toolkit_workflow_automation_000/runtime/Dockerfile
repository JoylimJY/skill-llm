FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# Install finml-toolkit from public git source (simulated as a local bash script install)
# We'll install it as a shell script in /usr/local/bin
RUN pip3 install --break-system-packages j2 2>/dev/null || true

WORKDIR /workspace