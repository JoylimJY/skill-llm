FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    xmlstarlet \
    jq \
    unzip \
    zip \
    python3 \
    python3-pip \
    bash \
    coreutils \
    && rm -rf /var/lib/apt/lists/*