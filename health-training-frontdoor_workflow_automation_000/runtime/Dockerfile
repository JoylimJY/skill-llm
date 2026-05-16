FROM node:18-bullseye

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    jq \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip
RUN pip3 install requests

WORKDIR /workspace