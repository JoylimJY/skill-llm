FROM node:20-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages beautifulsoup4 lxml requests

RUN echo '{"name": "maya-portfolio", "version": "1.0.0", "scripts": {"start": "python3 -m http.server 3000"}}' > package.json

RUN npm install

COPY . .

EXPOSE 3000