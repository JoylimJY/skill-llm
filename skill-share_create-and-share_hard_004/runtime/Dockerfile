FROM python:3.11-slim
RUN apt-get update && apt-get install -y curl git zip unzip && rm -rf /var/lib/apt/lists/*
RUN pip install requests pyyaml slack-sdk
WORKDIR /workspace