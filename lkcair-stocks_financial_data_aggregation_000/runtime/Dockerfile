FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash user
USER user
WORKDIR /home/user

# Clone the yfinance-ai skill repository
RUN git clone https://github.com/lkcair/yfinance-ai.git /home/user/stocks

WORKDIR /home/user/stocks

# Create the virtual environment and install dependencies
RUN python3 -m venv .venv && \
    .venv/bin/python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    .venv/bin/python3 -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    .venv/bin/python3 -m pip install pydantic -i https://pypi.tuna.tsinghua.edu.cn/simple

# Eval dependencies
RUN .venv/bin/python3 -m pip install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /home/user