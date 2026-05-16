FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# Install ONLY what read_file.py needs (standard library only, no openpyxl, no python-docx)
# We intentionally do NOT install openpyxl or python-docx so agent cannot bypass the skill script
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    lxml

# Create the skill directory structure matching the SKILL.md's described location
RUN mkdir -p /skills/encrypted-file-reader

WORKDIR /workspace