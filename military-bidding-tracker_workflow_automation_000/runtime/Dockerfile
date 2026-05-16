FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install requests python-dotenv -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install milb-tracker from the workspace (will be installed in setup_script after workspace is ready)
# We need the package to exist first, so install dependencies only
RUN pip install click rich -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace