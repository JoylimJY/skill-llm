FROM node:20-slim

RUN apt-get update && apt-get install -y \
    curl \
    jq \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages requests beautifulsoup4 lxml

WORKDIR /workspace

RUN npm init -y && npm install --save \
    @modelcontextprotocol/sdk \
    axios \
    zod \
    express \
    @types/node \
    tsx \
    typescript

RUN npx tsc --init --target ES2022 --module Node16 --moduleResolution Node16 --outDir ./dist --rootDir ./src --strict --esModuleInterop

CMD ["/bin/bash"]