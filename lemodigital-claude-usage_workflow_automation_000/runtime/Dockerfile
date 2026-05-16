FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install requests python-dateutil pytz -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install the claude-usage skill from the public repo
RUN mkdir -p /opt/skills/claude-usage/scripts && \
    pip install claude-usage 2>/dev/null || true

# Clone the actual skill repo for the script
RUN git clone https://github.com/ccc0168/claude-usage-calculator /opt/skills/claude-usage 2>/dev/null || \
    mkdir -p /opt/skills/claude-usage/scripts

WORKDIR /workspace