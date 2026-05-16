FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install requests colorama rich click -i https://pypi.tuna.tsinghua.edu.cn/simple

# Clone the token-optimizer tool into /opt/token-optimizer
RUN git clone https://github.com/smartpeopleconnected/openclaw-token-optimizer.git /opt/token-optimizer || true

WORKDIR /workspace