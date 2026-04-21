FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    file \
    md5deep \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pillow

WORKDIR /workspace

CMD ["/bin/bash"]