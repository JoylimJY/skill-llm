FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget \
    xfonts-75dpi \
    xfonts-base \
    fonts-liberation \
    fonts-dejavu-core \
    && wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.bullseye_amd64.deb \
    && dpkg -i wkhtmltox_0.12.6.1-2.bullseye_amd64.deb || apt-get install -f -y \
    && rm wkhtmltox_0.12.6.1-2.bullseye_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --break-system-packages \
    python-pptx==0.6.23 \
    reportlab==4.0.4 \
    pillow==10.0.0 \
    python-docx==0.8.11 \
    beautifulsoup4==4.12.2 \
    lxml==4.9.3

WORKDIR /workspace