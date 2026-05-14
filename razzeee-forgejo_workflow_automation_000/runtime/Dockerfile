FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    jq \
    python3 \
    python3-pip \
    golang-go \
    ca-certificates \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install tea CLI via go
RUN go install code.gitea.io/tea@latest

# Make sure tea is in PATH
ENV PATH="/root/go/bin:${PATH}"

# Install Python packages for mock server and eval
RUN pip3 install flask requests --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace