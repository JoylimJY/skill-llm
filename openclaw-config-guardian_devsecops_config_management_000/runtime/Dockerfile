FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || \
    sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    inotify-tools \
    jq \
    curl \
    wget \
    git \
    sudo \
    bash \
    coreutils \
    procps \
    systemd \
    systemd-sysv \
    python3 \
    python3-pip \
    && apt-get clean

# We need systemd to work minimally; use a lightweight approach
# The guardian install.sh registers a systemd unit, so systemd must be available

WORKDIR /workspace

CMD ["/bin/bash"]