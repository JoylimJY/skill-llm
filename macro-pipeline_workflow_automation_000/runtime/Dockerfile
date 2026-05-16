FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    bash \
    coreutils \
    findutils \
    grep \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple \
    pytest \
    pyyaml

# Set up a realistic home directory structure
RUN useradd -m -s /bin/bash bioagent
WORKDIR /home/bioagent
ENV HOME=/home/bioagent

CMD ["/bin/bash"]