FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    uuid-runtime \
    jq \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install jsonschema python-dateutil -i https://pypi.tuna.tsinghua.edu.cn/simple