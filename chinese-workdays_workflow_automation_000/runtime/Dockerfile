FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pyyaml -i https://pypi.tuna.tsinghua.edu.cn/simple

# Clone the chinese-workdays skill into /opt/skill
RUN git clone https://github.com/loonghao/chinese-workdays.git /opt/skill || \
    (mkdir -p /opt/skill && echo "clone failed")

WORKDIR /workspace