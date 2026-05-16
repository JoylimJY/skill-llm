FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    fontconfig \
    wget \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN pip install python-pptx Pillow lxml -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install Poppins and Lora fonts system-wide
RUN mkdir -p /usr/share/fonts/truetype/poppins && \
    mkdir -p /usr/share/fonts/truetype/lora

RUN wget -q "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf" \
    -O /usr/share/fonts/truetype/poppins/Poppins-Regular.ttf 2>/dev/null || true && \
    wget -q "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf" \
    -O /usr/share/fonts/truetype/poppins/Poppins-Bold.ttf 2>/dev/null || true && \
    wget -q "https://github.com/google/fonts/raw/main/ofl/lora/Lora%5Bwght%5D.ttf" \
    -O /usr/share/fonts/truetype/lora/Lora-Regular.ttf 2>/dev/null || true

RUN fc-cache -f -v 2>/dev/null || true

WORKDIR /workspace