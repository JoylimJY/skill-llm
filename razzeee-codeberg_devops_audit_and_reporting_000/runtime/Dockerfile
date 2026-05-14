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
    sqlite3 \
    ca-certificates \
    gnupg \
    lsb-release \
    supervisor \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install tea CLI via go
RUN go install code.gitea.io/tea@latest
RUN cp /root/go/bin/tea /usr/local/bin/tea

# Install Gitea (Forgejo-compatible) as local mock server
RUN wget -q -O /usr/local/bin/gitea \
    "https://dl.gitea.com/gitea/1.21.11/gitea-1.21.11-linux-amd64" \
    && chmod +x /usr/local/bin/gitea

RUN pip3 install requests -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace