FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget \
    xvfb \
    fonts-liberation \
    libfontconfig1 \
    fontconfig \
    libjpeg62-turbo \
    libpng16-16 \
    libssl3 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    xfonts-75dpi \
    xfonts-base \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.bullseye_amd64.deb \
    && dpkg -i wkhtmltox_0.12.6.1-2.bullseye_amd64.deb || true \
    && apt-get install -f -y \
    && rm wkhtmltox_0.12.6.1-2.bullseye_amd64.deb

RUN pip install --break-system-packages \
    python-pptx==0.6.21 \
    Pillow==10.0.0 \
    reportlab==4.0.4 \
    pdfkit==1.0.0 \
    beautifulsoup4==4.12.2 \
    lxml==4.9.3 \
    colorama==0.4.6

WORKDIR /workspace