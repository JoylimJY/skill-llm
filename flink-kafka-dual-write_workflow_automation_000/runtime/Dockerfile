FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    openjdk-17-jdk-headless \
    maven \
    curl \
    wget \
    git \
    tree \
    && apt-get clean

RUN pip3 install javalang -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages