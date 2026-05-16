FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    fd-find \
    python3 \
    python3-pip \
    coreutils \
    bash \
    && rm -rf /var/lib/apt/lists/*

# fd-find on Debian installs as 'fdfind', create symlink for 'fd'
RUN ln -sf /usr/bin/fdfind /usr/local/bin/fd

WORKDIR /workspace