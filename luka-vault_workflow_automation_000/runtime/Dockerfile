FROM python:3.13-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -Lsf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:/root/.local/bin:$PATH"

# Install researchvault from PyPI/git
RUN uv pip install --system researchvault -i https://pypi.tuna.tsinghua.edu.cn/simple || true

WORKDIR /workspace