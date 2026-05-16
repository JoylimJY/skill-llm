FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    jq \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    requests \
    python-dotenv \
    pydantic \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create venv to match the skill's entrypoint (.venv/bin/python)
RUN python -m venv /workspace/.venv && \
    /workspace/.venv/bin/pip install --no-cache-dir \
    requests \
    python-dotenv \
    pydantic \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace