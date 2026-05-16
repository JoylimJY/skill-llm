FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    locales \
    && rm -rf /var/lib/apt/lists/*

RUN sed -i '/zh_CN.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

ENV LANG=zh_CN.UTF-8
ENV LC_ALL=zh_CN.UTF-8

RUN pip install \
    zhdate \
    pypinyin \
    opencc-python-reimplemented \
    holidays \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace