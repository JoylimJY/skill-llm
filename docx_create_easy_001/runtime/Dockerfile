FROM node:20-slim
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN npm install -g docx
RUN pip3 install --break-system-packages python-docx lxml