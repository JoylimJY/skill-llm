FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN pip install python-docx -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install the md2word-cn skill
RUN mkdir -p /root/.agents/skills/md2word-cn/scripts

RUN pip install python-docx -i https://pypi.tuna.tsinghua.edu.cn/simple