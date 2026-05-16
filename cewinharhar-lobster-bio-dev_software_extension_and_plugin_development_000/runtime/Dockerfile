FROM python:3.12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    pytest \
    pytest-cov \
    anndata \
    numpy \
    scipy \
    pandas \
    setuptools \
    wheel \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install a minimal lobster-ai core stub so imports resolve
RUN pip install \
    langchain-core \
    langgraph \
    langchain \
    pydantic \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace