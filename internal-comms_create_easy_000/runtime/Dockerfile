FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    jq \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

CMD ["bash"]
