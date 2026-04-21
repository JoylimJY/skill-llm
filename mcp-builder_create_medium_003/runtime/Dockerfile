FROM node:20-slim
WORKDIR /workspace
RUN npm install -g typescript ts-node
RUN npm install @modelcontextprotocol/sdk zod axios
COPY . .
RUN npm install
RUN if [ -f package.json ] && grep -q '"build"[[:space:]]*:' package.json; then npm run build; fi
CMD ["/bin/bash"]