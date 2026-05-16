FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    bash \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create a stub 'codex' binary so the skill's bin requirement is satisfied
RUN echo '#!/bin/bash\nexit 0' > /usr/local/bin/codex && chmod +x /usr/local/bin/codex

WORKDIR /workspace