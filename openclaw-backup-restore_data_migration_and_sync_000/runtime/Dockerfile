FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    rsync \
    python3 \
    python3-pip \
    curl \
    bash \
    jq \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

# Set up a non-root user for realistic HOME dir behavior
RUN useradd -m -s /bin/bash devops && \
    git config --global user.email "devops@example.com" && \
    git config --global user.name "DevOps Agent"

WORKDIR /home/devops
ENV HOME=/home/devops
ENV USER=devops

# Configure git globally for the devops user
RUN su devops -c "git config --global user.email 'devops@example.com' && git config --global user.name 'DevOps Agent' && git config --global init.defaultBranch main"