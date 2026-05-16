FROM debian:12

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    openssh-server \
    openssh-client \
    default-mysql-server \
    default-mysql-client \
    python3 \
    python3-pip \
    curl \
    wget \
    netcat-openbsd \
    sudo \
    vim \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pymysql tabulate -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

RUN mkdir -p /run/sshd