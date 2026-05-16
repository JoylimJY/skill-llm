FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN pip install requests fastapi uvicorn -i https://pypi.tuna.tsinghua.edu.cn/simple

# Clone the soul-memory repository
RUN git clone https://github.com/kingofqin2026/Soul-Memory-.git /opt/soul-memory || true

WORKDIR /workspace