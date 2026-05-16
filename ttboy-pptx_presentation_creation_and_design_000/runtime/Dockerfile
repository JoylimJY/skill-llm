FROM node:20-bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    poppler-utils \
    libreoffice \
    curl \
    wget \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install "markitdown[pptx]" Pillow defusedxml python-pptx lxml -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

RUN npm install -g pptxgenjs react react-dom react-icons sharp

WORKDIR /workspace