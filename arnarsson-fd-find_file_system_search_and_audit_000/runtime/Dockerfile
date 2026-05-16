FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    fd-find \
    git \
    python3 \
    python3-pip \
    coreutils \
    findutils \
    bash \
    && rm -rf /var/lib/apt/lists/*

# fd-find installs as 'fdfind' on Debian; create alias
RUN ln -sf /usr/bin/fdfind /usr/local/bin/fd

WORKDIR /workspace