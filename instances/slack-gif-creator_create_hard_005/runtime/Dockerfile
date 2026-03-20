FROM python:3.11-slim
RUN apt-get update && apt-get install -y libfreetype6-dev libjpeg-dev zlib1g-dev && rm -rf /var/lib/apt/lists/*
RUN pip install pillow imageio numpy
WORKDIR /workspace