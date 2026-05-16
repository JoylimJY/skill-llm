FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    openai \
    anthropic \
    litellm \
    sqlite-utils \
    pandas \
    numpy \
    python-dotenv \
    requests \
    tiktoken \
    tenacity \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace