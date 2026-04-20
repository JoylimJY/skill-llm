FROM node:20-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
RUN npm init -y && npm install aap-agent-server aap-agent-client && npm cache clean --force