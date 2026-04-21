FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libxml2-dev \
       libxslt-dev \
       libffi-dev \
       libbz2-dev \
       liblzma-dev \
       libsqlite3-dev \
       python3-pip \
       curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir openpyxl

# The framework mounts source code and input files, so no copy needed
CMD ["/bin/bash"]
