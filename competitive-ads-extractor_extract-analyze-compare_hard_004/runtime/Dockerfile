FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    imagemagick \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pillow markdown

WORKDIR /workspace

CMD ["/bin/bash"]
