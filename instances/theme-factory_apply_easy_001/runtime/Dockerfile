FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    poppler-utils \
    wget \
    xfonts-75dpi \
    xfonts-base \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb \
    && dpkg -i wkhtmltox_0.12.6.1-2.jammy_amd64.deb || apt-get install -f -y \
    && rm wkhtmltox_0.12.6.1-2.jammy_amd64.deb

RUN pip install --no-cache-dir \
    python-pptx==0.6.23 \
    jinja2==3.1.2 \
    pdfkit==1.0.0 \
    Pillow==10.0.0

WORKDIR /workspace