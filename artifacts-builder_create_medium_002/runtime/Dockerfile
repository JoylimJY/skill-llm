FROM node:20-slim

# Install bash and python for eval scripts
RUN apt-get update && apt-get install -y bash python3 python3-pip && rm -rf /var/lib/apt/lists/*

# Install pnpm globally
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /workspace

# No extra copies - scripts and inputs mounted dynamically

CMD ["bash"]