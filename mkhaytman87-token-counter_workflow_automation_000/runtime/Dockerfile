FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    jq \
    uuid-runtime \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    jsonlines \
    python-dateutil \
    tabulate \
    click \
    rich

ENV OPENCLAW_DATA_DIR=/workspace/openclaw_data
ENV OPENCLAW_SKILLS_DIR=/workspace/openclaw_skills
ENV OPENCLAW_WORKSPACE=/workspace/openclaw_workspace

WORKDIR /workspace