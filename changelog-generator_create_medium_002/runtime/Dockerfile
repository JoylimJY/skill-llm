FROM python:3.11-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir gitpython --break-system-packages

WORKDIR /workspace

RUN git config --global init.defaultBranch main \
    && git config --global user.name "Test User" \
    && git config --global user.email "testuser@example.com"

CMD ["bash"]