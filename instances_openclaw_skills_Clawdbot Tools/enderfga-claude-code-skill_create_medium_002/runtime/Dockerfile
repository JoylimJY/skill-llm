FROM node:20-slim

RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN npm install -g @openclaw/claude-code-skill
RUN python3 --version