FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libjpeg62-turbo-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --break-system-packages requests beautifulsoup4 markdownify pillow

ENV LANG C.UTF-8

WORKDIR /app

CMD ["python3"]