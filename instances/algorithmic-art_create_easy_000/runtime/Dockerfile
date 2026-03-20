FROM node:20-slim
RUN apt-get update && apt-get install -y python3 python3-pip curl
RUN pip3 install --break-system-packages beautifulsoup4 lxml requests
WORKDIR /workspace