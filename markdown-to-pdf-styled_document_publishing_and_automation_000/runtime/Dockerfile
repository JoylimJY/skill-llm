FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    pandoc \
    wkhtmltopdf \
    xvfb \
    python3 \
    python3-pip \
    curl \
    bash \
    file \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pypdf PyPDF2 -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

# Create a wrapper for wkhtmltopdf to work headlessly
RUN printf '#!/bin/bash\nxvfb-run -a --server-args="-screen 0 1024x768x24" /usr/bin/wkhtmltopdf "$@"\n' > /usr/local/bin/wkhtmltopdf-headless && \
    chmod +x /usr/local/bin/wkhtmltopdf-headless