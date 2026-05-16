FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    coreutils \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Create workspace-scoped venv and install biopython + pandas inside it
RUN python -m venv /workspace/.venv-bio && \
    /workspace/.venv-bio/bin/pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    /workspace/.venv-bio/bin/pip install biopython==1.83 pandas==2.2.2 -i https://pypi.tuna.tsinghua.edu.cn/simple

# Also ensure python3 globally has nothing special (to force workspace-scoped path usage)
RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace