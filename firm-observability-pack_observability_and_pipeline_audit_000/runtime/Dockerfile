FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    jq \
    sqlite3 \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    mcp-openclaw-extensions \
    jsonlines \
    requests \
    -i https://pypi.tuna.tsinghua.edu.cn/simple || true

# Install the firm-observability-pack skill tools as mock executables
# These will be created in the setup script
ENV PATH="/usr/local/bin/openclaw:$PATH"