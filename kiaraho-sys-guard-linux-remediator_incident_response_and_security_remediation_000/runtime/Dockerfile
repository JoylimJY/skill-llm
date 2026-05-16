FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    curl \
    iproute2 \
    iptables \
    net-tools \
    iputils-ping \
    coreutils \
    grep \
    gawk \
    procps \
    sudo \
    openssh-client \
    findutils \
    bash \
    && apt-get clean

RUN pip3 install requests -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

# Download Didier Stevens Suite tools
RUN mkdir -p /opt/forensics && \
    wget -q -P /opt/forensics https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/base64dump.py && \
    wget -q -P /opt/forensics https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/re-search.py && \
    wget -q -P /opt/forensics https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/zipdump.py && \
    wget -q -P /opt/forensics https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/1768.py && \
    wget -q -P /opt/forensics https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/pdf-parser.py && \
    wget -q -P /opt/forensics https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/oledump.py && \
    chmod +x /opt/forensics/*.py

RUN mkdir -p /etc/iptables && touch /etc/iptables/rules.v4

WORKDIR /workspace