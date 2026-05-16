FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    lunar-python \
    pytz \
    jinja2 \
    click \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN pip install \
    sxtwl \
    -i https://pypi.tuna.tsinghua.edu.cn/simple || true

# Install the bazi analysis skill
RUN pip install \
    bazi-tools \
    -i https://pypi.tuna.tsinghua.edu.cn/simple || true

WORKDIR /workspace