FROM node:20-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g live-server

RUN pip3 install --break-system-packages beautifulsoup4 requests selenium webdriver-manager

COPY . .

EXPOSE 8080

CMD ["bash"]