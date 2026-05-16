FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    bash \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -Ls https://astral.sh/uv/install.sh | bash
ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

RUN pip install toml -i https://pypi.tuna.tsinghua.edu.cn/simple

# Configure git so commits inside the container work
RUN git config --global user.email "agent@benchmark.local" && \
    git config --global user.name "BenchmarkAgent" && \
    git config --global init.defaultBranch main