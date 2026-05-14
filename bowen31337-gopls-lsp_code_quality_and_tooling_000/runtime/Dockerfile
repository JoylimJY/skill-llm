FROM golang:1.21-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pyyaml -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install gopls
RUN go install golang.org/x/tools/gopls@latest

# Ensure GOPATH/bin is in PATH
ENV PATH="/root/go/bin:${PATH}"
ENV GOPATH="/root/go"

WORKDIR /workspace