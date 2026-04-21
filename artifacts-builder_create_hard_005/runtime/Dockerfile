FROM node:20-slim

# Install git, curl, bash, python3, and nodejs to run Node scripts properly
RUN apt-get update && apt-get install -y git curl bash python3 nodejs && rm -rf /var/lib/apt/lists/*

# Install pnpm globally
RUN corepack enable && corepack prepare pnpm@7.29.1 --activate

WORKDIR /workspace

# Create scripts directory and bundle-artifact.sh script
RUN mkdir -p scripts && \
    echo '#!/bin/bash' > scripts/bundle-artifact.sh && \
    echo 'echo "Bundle script executed successfully"' >> scripts/bundle-artifact.sh && \
    chmod +x scripts/bundle-artifact.sh

# Create empty shadcn-components.tar.gz file in scripts directory
RUN touch scripts/shadcn-components.tar.gz

# We do NOT copy repo files here; gen_inputs_script and mounted scripts provide needed files

# We will run scripts/init-artifact.sh and bundle-artifact.sh via setup and task steps

# Expose a non-root user (optional, for security)
# RUN useradd -ms /bin/bash claudeuser
# USER claudeuser

ENV NODE_ENV=development