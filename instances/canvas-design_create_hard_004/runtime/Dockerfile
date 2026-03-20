FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    fontconfig \
    fonts-liberation \
    fonts-dejavu-core \
    fonts-noto \
    ghostscript \
    libfreetype6-dev \
    libjpeg62-turbo-dev \
    libpng-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    Pillow==10.0.0 \
    matplotlib==3.7.2 \
    reportlab==4.0.4 \
    numpy==1.24.3 \
    PyPDF2==3.0.1 \
    python-magic==0.4.27 \
    fonttools==4.42.1

WORKDIR /workspace

COPY . /workspace/

CMD ["bash"]