FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    xvfb \
    fonts-liberation \
    libjpeg-dev \
    zlib1g-dev \
    wget \
    xfonts-75dpi \
    xfonts-base \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bullseye_amd64.deb \
    && dpkg -i wkhtmltox_0.12.6.1-3.bullseye_amd64.deb || true \
    && apt-get update && apt-get install -f -y \
    && rm wkhtmltox_0.12.6.1-3.bullseye_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --break-system-packages \
    pandas==2.1.* \
    matplotlib==3.7.* \
    seaborn==0.12.* \
    plotly==5.17.* \
    reportlab==4.0.* \
    pdfkit==1.0.* \
    openpyxl==3.1.* \
    scikit-learn==1.3.* \
    jinja2==3.1.* \
    kaleido==0.2.*

WORKDIR /workspace