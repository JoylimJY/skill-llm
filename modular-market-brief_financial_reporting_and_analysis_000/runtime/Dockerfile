FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    bash \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Create the market-brief venv as skill specifies
RUN python3 -m venv /root/.venvs/market-brief \
    && /root/.venvs/market-brief/bin/pip install -U pip -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && /root/.venvs/market-brief/bin/pip install yfinance pandas numpy requests -i https://pypi.tuna.tsinghua.edu.cn/simple

# Also install for eval script
RUN pip install pandas numpy -i https://pypi.tuna.tsinghua.edu.cn/simple