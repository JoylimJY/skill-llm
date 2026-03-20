FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget \
    xvfb \
    fonts-dejavu-core \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && apt-get update \
    && apt-get install -y ./wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && rm wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    jinja2==3.1.2 \
    beautifulsoup4==4.12.2 \
    lxml==4.9.3 \
    pdfkit==1.0.0 \
    weasyprint==60.2 \
    reportlab==4.0.7 \
    Pillow==10.1.0

WORKDIR /workspace

COPY . .

ENV DISPLAY=:99