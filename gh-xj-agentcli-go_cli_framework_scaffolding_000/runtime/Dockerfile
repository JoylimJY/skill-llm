FROM golang:1.23-bookworm

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    jq \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install agentcli-go framework
RUN go install github.com/gh-xj/agentcli-go/cmd/agentcli@latest 2>/dev/null || true

# Set up Go environment
ENV GOPATH=/root/go
ENV PATH=$PATH:/root/go/bin

# Clone the agentcli-go library so it's available for reference and use
RUN git clone https://github.com/gh-xj/agentcli-go /opt/agentcli-go || true

WORKDIR /workspace