FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    scikit-learn \
    numpy \
    python-Levenshtein \
    click \
    rich \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install the ai-deterministic-control skill via pip (simulated as a local package)
# We will build it in the setup script from a local source tree

WORKDIR /workspace