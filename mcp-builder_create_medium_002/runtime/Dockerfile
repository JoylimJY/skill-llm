FROM node:20-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-minimal bash ca-certificates && rm -rf /var/lib/apt/lists/*

RUN npm install -g typescript ts-node

RUN npm install @modelcontextprotocol/sdk zod axios

COPY . .

RUN npm install

RUN if [ -f package.json ] && npm run | grep -qE '^[[:space:]]*build[[:space:]]'; then npm run build; fi

CMD ["/bin/bash"]