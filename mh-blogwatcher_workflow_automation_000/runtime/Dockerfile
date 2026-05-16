FROM golang:1.24-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    wget \
    jq \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install requests -i https://pypi.tuna.tsinghua.edu.cn/simple

# Configure Go proxy to use accessible mirror
ENV GOPROXY=https://goproxy.cn,direct

# Install blogwatcher
RUN go install github.com/Hyaxia/blogwatcher/cmd/blogwatcher@latest

# Ensure blogwatcher is on PATH
ENV PATH="/root/go/bin:${PATH}"

WORKDIR /workspace