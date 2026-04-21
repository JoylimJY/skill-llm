FROM node:20-slim
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
RUN if [ -f package.json ]; then npm install; fi
RUN pip3 install --break-system-packages beautifulsoup4 lxml