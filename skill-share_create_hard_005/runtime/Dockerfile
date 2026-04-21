FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    zip \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pyyaml \
    requests \
    jinja2

WORKDIR /workspace

CMD ["/bin/bash"]