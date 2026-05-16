FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    nmap \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    libcap2-bin \
    sudo \
    net-tools \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install fastmcp python-nmap pyyaml pytest requests -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

# Grant nmap raw socket capability for SYN/OS scans
RUN setcap cap_net_raw+ep $(which nmap) || true

WORKDIR /workspace