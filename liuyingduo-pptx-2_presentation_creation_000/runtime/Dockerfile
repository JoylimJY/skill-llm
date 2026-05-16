FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    curl \
    wget \
    unzip \
    libvips-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install \
    "markitdown[pptx]" \
    python-pptx \
    lxml \
    defusedxml \
    Pillow \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --break-system-packages

RUN mkdir -p /usr/local/lib/node_modules_shared && \
    cd /usr/local/lib/node_modules_shared && \
    npm install pptxgenjs react-icons react react-dom sharp

ENV NODE_PATH=/usr/local/lib/node_modules_shared/node_modules