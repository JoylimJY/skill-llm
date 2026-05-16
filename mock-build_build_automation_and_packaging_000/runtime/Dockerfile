FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    bash \
    coreutils \
    findutils \
    grep \
    sed \
    rpm \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest pyyaml -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

# Create mock group and user
RUN groupadd -r mock && useradd -r -g mock -m mockbuilder

# Create standard mock directory structure
RUN mkdir -p /etc/mock /var/lib/mock /var/cache/mock /var/log/mock

WORKDIR /workspace